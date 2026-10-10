"""The typed repair prompt."""

from lpgcast.llm.client import ChatMessage
from lpgcast.repair import INTRO, repair_messages, repair_prompt
from lpgcast.validate import Finding


def _finding(kind, path, **kwargs):
    return Finding(
        kind=kind,
        scope=kwargs.pop("scope", "vertex"),
        path=path,
        message=kwargs.pop("message", f"{kind} at {path}"),
        fragment=kwargs.pop("fragment", {"ref": "v1"}),
        **kwargs,
    )


def test_findings_are_grouped_in_a_fixed_kind_order():
    prompt = repair_prompt(
        [
            _finding("quote_not_found", "vertices[1]"),
            _finding("unknown_type", "vertices[0]", fragment={"type": "Robot"}),
            _finding("quote_not_found", "edges[0]", scope="edge"),
        ]
    )
    assert prompt.startswith(INTRO)
    assert prompt.index("## unknown_type") < prompt.index("## quote_not_found")
    assert prompt.count("## quote_not_found") == 1
    assert '{"type":"Robot"}' in prompt
    assert "`edges[0]`" in prompt


def test_consequences_are_not_listed():
    prompt = repair_prompt([_finding("endpoint_invalid", "edges[0]", scope="edge")])
    assert "endpoint_invalid" not in prompt


def test_prompt_is_deterministic():
    findings = [
        _finding("coercion", "vertices[0].props[0]", scope="property", detail="type")
    ]
    assert repair_prompt(findings) == repair_prompt(findings)


def test_messages_carry_the_request_the_reply_and_the_corrections():
    original: list[ChatMessage] = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "u"},
    ]
    messages = repair_messages(
        original, '{"vertices": []}', [_finding("unknown_type", "x")]
    )
    assert messages[:2] == original
    assert messages[2] == {"role": "assistant", "content": '{"vertices": []}'}
    assert messages[3]["role"] == "user"
    assert messages[3]["content"].startswith("# CORRECTIONS")
