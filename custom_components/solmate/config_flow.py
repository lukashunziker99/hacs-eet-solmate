from homeassistant import config_entries
import voluptuous as vol

class SolMateConfigFlow(config_entries.ConfigFlow, domain="solmate"):

    async def async_step_user(self, info=None):

        if info is not None:
            return self.async_create_entry(
                title="SolMate",
                data=info
            )

        schema = vol.Schema({
            vol.Required("host"): str,
            vol.Required("port", default=8080): int
        })

        return self.async_show_form(step_id="user", data_schema=schema)
