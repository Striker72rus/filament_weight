import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import voluptuous as vol

from .const import (
    DOMAIN,
    CONF_NAME,
    CONF_WEIGHT,
    CONF_COLOR_HEX,
    CONF_TYPE,
    CONF_BRAND,
    CONF_COST,
)

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


async def async_setup(hass, hass_config):
    # used only with GUI setup
    hass.data[DOMAIN] = hass_config.get(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    if entry.data:
        hass.config_entries.async_update_entry(entry, data={}, options=entry.data)

    # await hass.config_entries.async_forward_entry_setup(entry, "number")

    coro = hass.config_entries.async_forward_entry_setup(entry, "number")
    hass.async_create_task(coro)

    async def update_weight_service(call):
        entity_id = call.data.get("entity_id")
        weight = call.data.get("weight")
        if entity_id and weight is not None:
            await async_update_entry(hass, entity_id, weight)

    hass.services.async_register(
        DOMAIN,
        "update_weight",
        update_weight_service,
        schema=vol.Schema(
            {
                vol.Required("entity_id"): str,
                vol.Required("weight"): vol.Coerce(float),
            }
        ),
    )
    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True


async def update_listener(hass, entry):
    """Handle options update."""

    for config_entry_id, entity in hass.data[DOMAIN].items():
        if hasattr(entity, "entity_id"):
            if config_entry_id == entry.entry_id:
                foundEntity = entity
                entity_id = entity.entity_id

    if entity_id:
        current_weight = getattr(foundEntity, "state", None)

        updateWeight = True
        for name, value in entry.options.items():
            lastValue = getattr(foundEntity, name, None)
            if lastValue != value and name != CONF_WEIGHT:
                updateWeight = False
                _LOGGER.info(
                    "Need update attribute '%s' last value '%s' new value '%s'",
                    name,
                    lastValue,
                    value,
                )
                if name == CONF_COLOR_HEX:
                    await foundEntity.async_set_color_hex(value)
                elif name == CONF_TYPE:
                    await foundEntity.async_set_type(value)
                elif name == CONF_NAME:
                    await foundEntity.async_set_friendly_name(value)
                elif name == CONF_BRAND:
                    await foundEntity.async_set_brand(value)
                elif name == CONF_COST:
                    await foundEntity.async_set_cost(value)
            if name == "weight":
                newWeight = value

        if updateWeight:
            if current_weight != newWeight:
                _LOGGER.info(
                    "Need updateWeight last value '%s' new value '%s'",
                    current_weight,
                    newWeight,
                )
                await foundEntity.async_set_value(float(newWeight))

        return
    return


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    return await hass.config_entries.async_forward_entry_unload(entry, "number")


async def async_update_entry(
    hass: HomeAssistant,
    entity_id: str,
    weight: float = None,
    type: str = None,
    color_hex: str = None,
    color_rgb: str = None,
    friendly_name: str = None,
):
    """Update a specific entity with new parameters."""
    entity = next(
        (e for e in hass.data[DOMAIN].values() if e.entity_id == entity_id), None
    )
    if entity:
        if weight is not None:
            await entity.async_set_value(weight)
        if type is not None:
            await entity.async_set_type(type)
        if color_hex is not None:
            await entity.async_set_color_hex(color_hex)
        if color_rgb is not None:
            await entity.async_set_color_rgb(color_rgb)
        if friendly_name is not None:
            await entity.async_set_friendly_name(friendly_name)
