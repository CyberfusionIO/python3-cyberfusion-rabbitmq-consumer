import os
import pwd
from unittest import mock

import pytest
from pytest_mock import MockerFixture  # type: ignore[attr-defined]

from cyberfusion.Common.Systemd import CyberfusionUnit
from cyberfusion.RabbitMQConsumer.tests import (
    Channel,
    Connection,
    Lock,
    Method,
    Properties,
    RabbitMQ,
)
from cyberfusion.RabbitMQHandlers.exceptions.rabbitmq_consumer import (
    ServiceReloadError,
)
from cyberfusion.RabbitMQHandlers.exchanges import dx_service_reload

PARAMETERS_HANDLE = (
    "dx_service_reload",
    "fake",
    {
        "unit_name": "test.service",
    },
)


@pytest.mark.parametrize(
    "handle_parameters",
    [PARAMETERS_HANDLE],
    indirect=True,
)
def test_dx_service_reload_handle_calls(
    mocker: MockerFixture, handle_parameters: dict
):
    mocker.patch(
        "cyberfusion.Common.Systemd.CyberfusionUnit.reload",
        return_value=None,
    )

    spy_unit_init = mocker.spy(CyberfusionUnit, "__init__")
    spy_reload = mocker.spy(CyberfusionUnit, "reload")

    dx_service_reload.handle(**handle_parameters)

    spy_unit_init.assert_called_once_with(mocker.ANY, "test.service")
    spy_reload.assert_called_once_with()


@pytest.mark.parametrize(
    "handle_parameters",
    [PARAMETERS_HANDLE],
    indirect=True,
)
def test_dx_service_reload_handle_result_success(
    mocker: MockerFixture, handle_parameters: dict
):
    mocker.patch(
        "cyberfusion.Common.Systemd.CyberfusionUnit.reload",
        return_value=None,
    )

    result = dx_service_reload.handle(**handle_parameters)

    assert result == {
        "success": True,
        "message": "[test.service] Service reloaded",
        "data": {},
    }


@pytest.mark.parametrize(
    "handle_parameters",
    [PARAMETERS_HANDLE],
    indirect=True,
)
def test_dx_service_reload_handle_result_caught_failure(
    mocker: MockerFixture, handle_parameters: dict
):
    mocker.patch(
        "cyberfusion.Common.Systemd.CyberfusionUnit.reload",
        return_value=None,
    )

    with mock.patch(
        "cyberfusion.Common.Systemd.CyberfusionUnit.reload",
        side_effect=ServiceReloadError,
    ):
        result = dx_service_reload.handle(**handle_parameters)

    assert result == {
        "success": False,
        "message": "[test.service] Service could not be reloaded due to error",
        "data": {},
    }


@pytest.mark.parametrize(
    "handle_parameters",
    [PARAMETERS_HANDLE],
    indirect=True,
)
def test_dx_service_reload_handle_result_uncaught_failure(
    mocker: MockerFixture, handle_parameters: dict
):
    mocker.patch(
        "cyberfusion.Common.Systemd.CyberfusionUnit.reload",
        return_value=None,
    )

    with mock.patch(
        "cyberfusion.Common.Systemd.CyberfusionUnit.__init__",
        side_effect=Exception,
    ):
        result = dx_service_reload.handle(**handle_parameters)

    assert result == {
        "success": False,
        "message": "[test.service] An unexpected exception occurred",
        "data": {},
    }
