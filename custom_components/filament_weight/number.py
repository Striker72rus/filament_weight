import logging
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.number import (
    NumberEntity,
    NumberDeviceClass,
    PLATFORM_SCHEMA,
)
from .utils import generateId
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.restore_state import RestoreEntity
from .const import (
    DOMAIN,
    CONF_NAME,
    CONF_WEIGHT,
    CONF_COLOR_HEX,
    CONF_TYPE,
    CONF_COST,
    CONF_BRAND,
)

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_TYPE): cv.string,
        vol.Required(CONF_WEIGHT): cv.string,
        vol.Required(CONF_COLOR_HEX): cv.string,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    add_entities([FilamentWeight(config)], True)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    brandToId = ""

    if (
        CONF_BRAND in entry.options
        and entry.options[CONF_BRAND] is not None
        and entry.options[CONF_BRAND] != "unknown"
    ):
        brandToId = f"{entry.options[CONF_BRAND]}_"

    unique_id = generateId(
        entry.options[CONF_BRAND],
        entry.options[CONF_TYPE],
        entry.options[CONF_COLOR_HEX],
    )
    entity_id = f"number.{unique_id}"

    # Check if the entity already exists
    if FilamentWeight.entity_exists(hass, entity_id):
        return

    entity = FilamentWeight(entry.options, entry.entry_id)
    async_add_entities([entity], True)
    hass.data[DOMAIN][entry.entry_id] = entity


class FilamentWeight(NumberEntity, RestoreEntity):
    def __init__(self, config: dict, unique_id=None):
        self._attr_name = config.get(CONF_NAME, config[CONF_NAME])
        self.type = config.get(CONF_TYPE, config[CONF_TYPE])

        self.brand = (
            config.get(CONF_BRAND, config[CONF_BRAND]) if CONF_BRAND in config else None
        )
        self.cost = (
            config.get(CONF_COST, config[CONF_COST]) if CONF_COST in config else None
        )
        self.hex_code = config.get(CONF_COLOR_HEX, config[CONF_COLOR_HEX])
        self.rgb_code = self.hex_to_rgb(self.hex_code)

        # Formatted entity_id
        self._attr_unique_id = generateId(self.brand, self.type, self.hex_code)

        self._attr_entity_id = f"number.{self._attr_unique_id}"
        self.entity_id = f"number.{self._attr_unique_id}"

        self._attr_state = float(config.get(CONF_WEIGHT, 1000.00))
        self._attr_step = 0.01  # Step size set to 1
        self._attr_min_value = 0
        self._attr_max_value = 10000  # Max value set to 100

        self._attr_native_max_value = 10000
        self._attr_native_min_value = 0
        self._attr_native_step = 0.01

        self._attr_icon = "mdi:rotate-3d-variant"

        self._attr_device_class = NumberDeviceClass.WEIGHT
        self._attr_mode = "auto"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "type": self.type,
            "color_hex": f"{self.hex_code}",
            "color_rgb": self.rgb_code,
            "brand": self.brand,
            "cost": self.cost,
        }

    @staticmethod
    def entity_exists(hass, entity_id):
        """Check if an entity with the given entity_id already exists."""
        for entity in hass.data[DOMAIN].values():
            if hasattr(entity, "entity_id") and entity.entity_id == entity_id:
                return True
        return False

    @staticmethod
    def hex_to_rgb(hex_code):
        """Convert HEX to RGB."""
        return ",".join(
            str(int(hex_code.lstrip("#")[i : i + 2], 16)) for i in (0, 2, 4)
        )

    async def async_added_to_hass(self):
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state and state.state is not None:
            self._attr_state = float(state.state)

    def debug(self, message):
        _LOGGER.debug(f"{self._attr_name} | {message}")

    @property
    def state(self):
        return self._attr_state

    @state.setter
    def state(self, value):
        self._attr_state = value

    @property
    def step(self):
        return self._attr_step

    @property
    def min_value(self):
        return self._attr_min_value

    @property
    def max_value(self):
        return self._attr_max_value

    @property
    def mode(self):
        return self._attr_mode

    async def async_set_value(self, value: float) -> None:
        self._attr_state = value
        self.async_write_ha_state()

    async def async_set_color_hex(self, color_hex: str) -> None:
        """Set the color HEX and update the entity."""
        self.hex_code = color_hex
        self.rgb_code = self.hex_to_rgb(self.hex_code)
        self.async_write_ha_state()

    async def async_set_color_rgb(self, color_rgb: str) -> None:
        """Set the color RGB and update the entity."""
        self.rgb_code = color_rgb
        self.hex_code = self.rgb_to_hex(color_rgb)
        self.async_write_ha_state()

    async def async_set_type(self, type: str) -> None:
        """Set the type and update the entity."""
        self.type = type
        self.async_write_ha_state()

    async def async_set_brand(self, brand: str) -> None:
        """Set the brand and update the entity."""
        self.brand = brand
        self.async_write_ha_state()

    async def async_set_cost(self, cost: str) -> None:
        """Set the cost and update the entity."""
        self.cost = cost
        self.async_write_ha_state()

    async def async_set_friendly_name(self, friendly_name: str) -> None:
        """Set the friendly name and update the entity."""
        self._attr_name = friendly_name
        self.async_write_ha_state()
