import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, OptionsFlow, ConfigEntry
from homeassistant.core import callback

from .utils import generateId
from .const import (
    DOMAIN,
    CONF_NAME,
    CONF_WEIGHT,
    CONF_COLOR_HEX,
    CONF_TYPE,
    CONF_BRAND,
    CONF_COST,
    TYPE_OPTIONS,
    DEFAULT_TYPE_OPTIONS,
    BRAND_OPTIONS,
    DEFAULT_BRAND_OPTIONS,
)

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


def get_custom_brands(hass):
    # Получение настроек интеграции из конфигурации Home Assistant
    config = hass.data.get(DOMAIN, {})
    custom_brands = config.get("brands", [])
    if custom_brands:
        if "unknown" not in custom_brands:
            custom_brands.append("unknown")
        return custom_brands
    return BRAND_OPTIONS


def get_custom_type(hass):
    # Получение настроек интеграции из конфигурации Home Assistant
    config = hass.data.get(DOMAIN, {})
    custom_type = config.get("type", [])
    if custom_type:
        if "unknown" not in custom_type:
            custom_type.append("unknown")
        return custom_type
    return TYPE_OPTIONS


class ConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            # Validate input data
            try:
                user_input[CONF_WEIGHT] = float(user_input[CONF_WEIGHT])
                if user_input[CONF_WEIGHT] <= 0:
                    raise vol.Invalid("Weight must be greater than 0.")
                if (
                    not user_input[CONF_COLOR_HEX].startswith("#")
                    or len(user_input[CONF_COLOR_HEX].lstrip("#")) not in (6, 8)
                    or not all(
                        c in "0123456789abcdefABCDEF"
                        for c in user_input[CONF_COLOR_HEX].lstrip("#")
                    )
                ):
                    raise vol.Invalid(
                        "Color hex must be a 6 or 8 character hexadecimal string."
                    )
            except ValueError as e:
                _LOGGER.error("Invalid value for weight: %s", e)
                return self.async_show_form(
                    step_id="user",
                    data_schema=self._get_schema(user_input),
                    errors={"base": "invalid_value_weight"},
                )
            except vol.Invalid as e:
                _LOGGER.error("Invalid input: %s", e)
                return self.async_show_form(
                    step_id="user",
                    data_schema=self._get_schema(user_input),
                    errors={"base": f"invalid_value {e.error_message}"},
                )

            unique_id = generateId(
                user_input[CONF_BRAND],
                user_input[CONF_TYPE],
                user_input[CONF_COLOR_HEX],
            )
            entity_id = f"number.{unique_id}"

            # Check if the configuration entry already exists
            existing_entity = self.hass.states.get(entity_id)

            if existing_entity:
                return self.async_abort(reason="already_exists")

            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        # Получаем пользовательские бренды из configuration.yaml
        custom_brands = get_custom_brands(self.hass)
        custom_type = get_custom_type(self.hass)
        return self.async_show_form(
            step_id="user",
            data_schema=self._get_schema(
                custom_brands=custom_brands, custom_type=custom_type
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)

    def _get_schema(
        self, user_input=None, custom_brands=BRAND_OPTIONS, custom_type=TYPE_OPTIONS
    ):
        if user_input is None:
            user_input = {}
        return vol.Schema(
            {
                vol.Required(
                    CONF_NAME,
                    default=user_input.get(CONF_NAME, ""),
                ): cv.string,
                vol.Required(
                    CONF_TYPE, default=user_input.get(CONF_TYPE, DEFAULT_TYPE_OPTIONS)
                ): vol.In(custom_type),
                vol.Required(
                    CONF_WEIGHT, default=user_input.get(CONF_WEIGHT, 1000)
                ): cv.positive_float,
                vol.Required(
                    CONF_COLOR_HEX, default=user_input.get(CONF_COLOR_HEX, "")
                ): cv.string,
                vol.Optional(
                    CONF_BRAND,
                    default=user_input.get(CONF_BRAND, DEFAULT_BRAND_OPTIONS),
                    description={CONF_BRAND: "unknown"},
                ): vol.In(custom_brands),
                vol.Optional(
                    CONF_COST,
                    default=user_input.get(CONF_COST, ""),
                    description={CONF_COST: "unknown"},
                ): cv.string,
            }
        )


class OptionsFlowHandler(OptionsFlow):
    def __init__(self, config_entry: ConfigEntry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            # Validate input data
            try:
                user_input[CONF_WEIGHT] = float(user_input[CONF_WEIGHT])
                if user_input[CONF_WEIGHT] <= 0:
                    raise vol.Invalid("Weight must be greater than 0.")
                if (
                    not user_input[CONF_COLOR_HEX].startswith("#")
                    or len(user_input[CONF_COLOR_HEX].lstrip("#")) not in (6, 8)
                    or not all(
                        c in "0123456789abcdefABCDEF"
                        for c in user_input[CONF_COLOR_HEX].lstrip("#")
                    )
                ):
                    raise vol.Invalid(
                        "Color hex must be a 6 or 8 character hexadecimal string."
                    )
            except ValueError as e:
                _LOGGER.error("Invalid value for weight: %s", e)
                return self.async_show_form(
                    step_id="init",
                    data_schema=self._get_schema(),
                    errors={"base": f"invalid_value  {e.error_message}"},
                )
            except vol.Invalid as e:
                _LOGGER.error("Invalid input: %s", e)
                return self.async_show_form(
                    step_id="init",
                    data_schema=self._get_schema(),
                    errors={"base": f"invalid_value {e.error_message}"},
                )

            return self.async_create_entry(title="", data=user_input)

        # Получаем пользовательские бренды из configuration.yaml
        custom_brands = get_custom_brands(self.hass)
        custom_type = get_custom_type(self.hass)
        return self.async_show_form(
            step_id="init",
            data_schema=self._get_schema(
                custom_brands=custom_brands, custom_type=custom_type
            ),
        )

    def _get_schema(self, custom_brands=BRAND_OPTIONS, custom_type=TYPE_OPTIONS):
        return vol.Schema(
            {
                vol.Required(
                    CONF_NAME,
                    default=self.config_entry.options.get(
                        CONF_NAME, self.config_entry.data.get(CONF_NAME)
                    ),
                ): cv.string,
                vol.Required(
                    CONF_TYPE,
                    default=self.config_entry.options.get(
                        CONF_TYPE, self.config_entry.data.get(CONF_TYPE)
                    ),
                ): vol.In(custom_type),
                vol.Required(
                    CONF_WEIGHT,
                    default=self.config_entry.options.get(
                        CONF_WEIGHT, self.config_entry.data.get(CONF_WEIGHT)
                    ),
                ): cv.positive_float,
                vol.Required(
                    CONF_COLOR_HEX,
                    default=self.config_entry.options.get(
                        CONF_COLOR_HEX, self.config_entry.data.get(CONF_COLOR_HEX)
                    ),
                ): cv.string,
                vol.Optional(
                    CONF_BRAND,
                    default=self.config_entry.options.get(
                        CONF_BRAND, self.config_entry.data.get(CONF_BRAND)
                    ),
                    description={CONF_BRAND: "unknown"},
                ): vol.In(custom_brands),
                vol.Optional(
                    CONF_COST,
                    default=self.config_entry.options.get(
                        CONF_COST, self.config_entry.data.get(CONF_COST)
                    ),
                    description={CONF_COST: "unknown"},
                ): cv.string,
            }
        )
