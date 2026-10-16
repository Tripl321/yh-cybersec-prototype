"""Tester för shallot_cli.sim — determinism, fail-closed, inga hemligheter."""

import pytest

from shallot_cli import sim


def test_all_scenarios_known():
    assert set(sim.SCENARIOS) == {"success", "wrong-key", "timeout", "crc", "disconnect", "late-ack"}


def test_success_grants_rest_deny_fail_closed():
    for name in sim.SCENARIOS:
        res = sim.run_scenario(name)
        if name == "success":
            assert res["result"] == "AUTHENTICATED"
            assert res["decision"] == "grant"
            assert res["reason_code"] == 0
            assert res["ack"] == "0x01"
        else:
            assert res["result"] == "DENIED"
            assert res["decision"] == "deny (fail closed)"
            assert res["reason_code"] in (1, 4, 5, 6)
            assert res["ack"] == "0x00"


def test_expected_reason_codes():
    assert sim.run_scenario("wrong-key")["reason_code"] == 5  # HMAC_MISMATCH
    assert sim.run_scenario("crc")["reason_code"] == 4  # PARSE_ERROR
    assert sim.run_scenario("disconnect")["reason_code"] == 6  # DISCONNECT
    assert sim.run_scenario("timeout")["reason_code"] == 1  # TIMEOUT
    assert sim.run_scenario("late-ack")["reason_code"] == 1  # TIMEOUT


def test_deterministic():
    first_success = sim.run_scenario("success")
    second_success = sim.run_scenario("success")
    first_wrong_key = sim.run_scenario("wrong-key")
    second_wrong_key = sim.run_scenario("wrong-key")
    assert first_success == second_success
    assert first_wrong_key == second_wrong_key


def test_unknown_scenario():
    with pytest.raises(ValueError):
        sim.run_scenario("unlock")


def test_render_banner_and_required_fields():
    for name in sim.SCENARIOS:
        text = sim.render(sim.run_scenario(name))
        assert "SIMULATED / TEST-ONLY" in text
        assert sim.TEST_NONCE.hex() in text
        assert "CHALLENGE" in text and "RESPONSE" in text
        assert "DENIED" in text or "AUTHENTICATED" in text
        assert "fail closed" in text or "grant" in text


def test_no_secret_keys_in_output():
    secrets = [
        sim.TEST_MASTER.hex(),
        sim.WRONG_MASTER.hex(),
        sim.derive_k_mac(sim.TEST_MASTER).hex(),
        sim.derive_k_mac(sim.WRONG_MASTER).hex(),
    ]
    for name in sim.SCENARIOS:
        text = sim.render(sim.run_scenario(name))
        for secret in secrets:
            assert secret not in text
