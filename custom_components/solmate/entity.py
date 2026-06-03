from homeassistant.helpers.entity import DeviceInfo

class SolMateEntity:

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={("solmate", "main")},
            name="EET SolMate",
            manufacturer="EET",
            model="SolMate",
        )

    @property
    def available(self):
        return self.coordinator.data is not None
