"""Unit tests for Windows Wi-Fi detector and LinkInfo quality threshold evaluation."""
import unittest
from unittest.mock import patch, MagicMock
from wifi_ac_guardian_win.core.models import BssidCandidate, LinkInfo, PhyMode, RadioState, GuardianConfig
from wifi_ac_guardian_win.core.detector_win import parse_netsh_bssid_candidates, parse_netsh_interfaces, parse_netsh_output, WifiDetectorWin


class TestWifiDetector(unittest.TestCase):
    def test_good_vht_high_bitrate(self):
        sample_output = """
        Name                   : Wi-Fi
        State                  : connected
        SSID                   : lab5g
        BSSID                  : 00:11:22:33:44:55
        Radio type             : 802.11ac
        Channel                : 36
        Signal                 : 95%
        Receive rate (Mbps)    : 866.7
        Transmit rate (Mbps)   : 866.7
        """
        link = parse_netsh_output(sample_output)
        self.assertTrue(link.connected)
        self.assertEqual(link.phy_mode, PhyMode.VHT)
        self.assertGreater(link.max_bitrate_mbps, 300.0)
        self.assertTrue(link.is_good(min_bitrate_threshold=300.0))

    def test_good_vht_433mbps_single_stream(self):
        sample_output = """
        Name                   : Wi-Fi
        State                  : connected
        SSID                   : lab5g
        Radio type             : 802.11ac
        Receive rate (Mbps)    : 433.3
        Transmit rate (Mbps)   : 433.3
        """
        link = parse_netsh_output(sample_output)
        self.assertEqual(link.phy_mode, PhyMode.VHT)
        self.assertTrue(link.is_good(min_bitrate_threshold=300.0))

    def test_downgraded_ht_low_bitrate(self):
        sample_output = """
        Name                   : Wi-Fi
        State                  : connected
        SSID                   : lab5g
        Radio type             : 802.11n
        Transmit rate (Mbps)   : 144
        Receive rate (Mbps)    : 144
        """
        link = parse_netsh_output(sample_output)
        self.assertTrue(link.connected)
        self.assertEqual(link.phy_mode, PhyMode.HT)
        self.assertLessEqual(link.max_bitrate_mbps, 300.0)
        self.assertFalse(link.is_good(min_bitrate_threshold=300.0))

    def test_downgraded_vht_300mbps_limit(self):
        sample_output = """
        Name                   : Wi-Fi
        State                  : connected
        SSID                   : lab5g
        Radio type             : 802.11ac
        Transmit rate (Mbps)   : 300
        Receive rate (Mbps)    : 300
        """
        link = parse_netsh_output(sample_output)
        self.assertTrue(link.connected)
        self.assertEqual(link.phy_mode, PhyMode.VHT)
        self.assertEqual(link.max_bitrate_mbps, 300.0)
        # Policy requires a rate strictly greater than 300 Mbps, so an exact
        # 300 Mbps Wi-Fi 5 reading remains actionable as degraded.
        self.assertFalse(link.is_good(min_bitrate_threshold=300.0))

    def test_parses_target_bssid_candidates_without_mixing_other_ssids(self):
        raw_output = """
        SSID 1 : lab5g
            BSSID 1 : 08:5c:1b:17:7d:80
                 Signal             : 95%
                 Radio type         : 802.11ac
                 Channel            : 161
            BSSID 2 : 08:5c:1b:17:7d:81
                 Signal             : 100%
                 Radio type         : 802.11n
                 Channel            : 6
        SSID 2 : Other Network
            BSSID 1 : aa:bb:cc:dd:ee:ff
                 Signal             : 99%
                 Radio type         : 802.11ax
                 Channel            : 149
        """
        candidates = parse_netsh_bssid_candidates(raw_output, "lab5g")

        self.assertEqual([candidate.bssid for candidate in candidates], ["08:5c:1b:17:7d:80", "08:5c:1b:17:7d:81"])
        self.assertEqual(candidates[0].band, "5GHz")
        self.assertEqual(candidates[0].phy_mode, PhyMode.VHT)
        self.assertEqual(candidates[1].band, "2.4GHz")

    def test_dynamic_selection_prefers_connected_oem_named_adapter(self):
        """The active adapter is discovered from Windows output, not assumed to be named Wi-Fi."""
        sample_output = """
        There are 2 interfaces on the system:

            Name                   : Wireless Network Connection
            Description            : Intel(R) Dual Band Wireless-AC 8265
            State                  : disconnected

            Name                   : WLAN-Office
            Description            : Realtek 8852CE WiFi 6E PCI-E NIC
            State                  : connected
            SSID                   : Office-5G
            Radio type             : 802.11ax
            Receive rate (Mbps)    : 1201
            Transmit rate (Mbps)   : 1201
        """
        links = parse_netsh_interfaces(sample_output)
        detector = WifiDetectorWin()
        selected = detector._select_interface(links)

        self.assertEqual(len(links), 2)
        self.assertEqual(selected.interface, "WLAN-Office")
        self.assertEqual(selected.adapter, "Realtek 8852CE WiFi 6E PCI-E NIC")
        self.assertEqual(selected.ssid, "Office-5G")
        self.assertEqual(selected.phy_mode, PhyMode.HE)

    def test_explicit_interface_override_remains_available_for_advanced_support(self):
        """An optional customer-selected interface override takes precedence over auto-discovery."""
        primary = LinkInfo(connected=True, interface="WLAN-Office", ssid="Office-5G")
        support_override = LinkInfo(connected=False, interface="Wireless Network Connection")
        detector = WifiDetectorWin(interface="Wireless Network Connection")

        selected = detector._select_interface([primary, support_override])

        self.assertEqual(selected.interface, "Wireless Network Connection")

    def test_unparsed_output_has_no_shipped_interface_name(self):
        """New installations do not invent the generic Wi-Fi interface name when Windows reports none."""
        link = parse_netsh_output("There is no wireless interface on the system.")

        self.assertEqual(link.interface, "")
        self.assertFalse(link.connected)

    def test_disconnected_interface_clears_signal_and_link_rates(self):
        """A user-disconnected Wi-Fi link must not retain stale quality metrics."""
        sample_output = """
            Name                   : WLAN-Office
            Description            : Realtek 8852CE WiFi 6E PCI-E NIC
            State                  : disconnected
            Signal                 : 96%
            Receive rate (Mbps)    : 1201
            Transmit rate (Mbps)   : 1201
        """
        link = parse_netsh_output(sample_output)

        self.assertFalse(link.connected)
        self.assertEqual(link.radio_state, RadioState.DISCONNECTED)
        self.assertEqual(link.signal_pct, 0)
        self.assertEqual(link.max_bitrate_mbps, 0)

    def test_radio_off_clears_live_link_values_but_keeps_physical_adapter_identity(self):
        """Airplane Mode/radio-off is not an adapter disable and must render separately."""
        detector = WifiDetectorWin()
        active = LinkInfo(
            connected=True,
            interface="WLAN-Office",
            adapter="Realtek 8852CE WiFi 6E PCI-E NIC",
            ssid="Office-5G",
            signal_pct=93,
            rx_bitrate="1201 Mbps",
            tx_bitrate="1201 Mbps",
            phy_mode=PhyMode.HE,
            radio_state=RadioState.ACTIVE,
        )
        with patch.object(detector, "get_interface_links", return_value=[active]), patch.object(
            detector, "_get_radio_state", return_value=RadioState.RADIO_OFF
        ):
            link = detector.get_link_info()

        self.assertFalse(link.connected)
        self.assertEqual(link.radio_state, RadioState.RADIO_OFF)
        self.assertEqual(link.adapter, "Realtek 8852CE WiFi 6E PCI-E NIC")
        self.assertEqual(link.signal_pct, 0)
        self.assertEqual(link.max_bitrate_mbps, 0)

    def test_disabled_adapter_hides_adapter_identity_from_live_telemetry(self):
        """A disabled adapter is reported as unavailable, not as a live device."""
        detector = WifiDetectorWin()
        disabled = LinkInfo(
            connected=False,
            phy_mode=PhyMode.DISCONNECTED,
            radio_state=RadioState.ADAPTER_DISABLED,
            signal_pct=0,
        )
        with patch.object(detector, "get_interface_links", return_value=[LinkInfo()]), patch.object(
            detector, "_get_unreported_adapter_state", return_value=disabled
        ):
            link = detector.get_link_info()

        self.assertEqual(link.radio_state, RadioState.ADAPTER_DISABLED)
        self.assertFalse(link.has_available_adapter)
        self.assertIsNone(link.adapter)
        self.assertEqual(link.max_bitrate_mbps, 0)


if __name__ == "__main__":
    unittest.main()
