from homeassistant.helpers.entity import DeviceInfo

class SolMateEntity:

    def __init__(self, coordinator):
        self.coordinator = coordinator

    @property
    def available(self):
        return self.coordinator.data is not None

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={("solmate", "main")},
            name="EET SolMate",
            manufacturer="EET",
            model="SolMate",
        )
