from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - exercised when dependency is absent
    raise SystemExit("PyYAML is required. Install with: python -m pip install pyyaml") from exc


KEBAB = re.compile(r"^[a-z0-9][a-z0-9-]*$")
CS_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class ModelError(Exception):
    pass


def load_model(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        model = yaml.safe_load(handle)
    if not isinstance(model, dict):
        raise ModelError("model root must be an object")
    return model


def validate_model(model: dict[str, Any], model_path: Path) -> list[str]:
    errors: list[str] = []
    if model.get("schema_version") != "middle-core-model.v1":
        errors.append("schema_version must be middle-core-model.v1")

    use_cases = id_set(model, "use_cases", errors)
    object_types = id_set(model, "object_types", errors)
    relationship_types = id_set(model, "relationship_types", errors)
    state_machines = id_set(model, "state_machines", errors)
    workflow_steps = id_set(model, "workflow_steps", errors)
    scenarios = id_set(model, "scenarios", errors)
    projections = id_set(model, "projections", errors)
    data_objects = name_set(model, "data_objects", errors)
    data_object_props = {
        item.get("name"): set(item["properties"].keys())
        for item in list_items(model, "data_objects")
        if isinstance(item.get("name"), str) and isinstance(item.get("properties"), dict)
    }

    for section in ["object_types", "relationship_types", "state_machines", "workflow_steps", "scenarios", "projections"]:
        for item in list_items(model, section):
            item_id = item.get("id")
            if not isinstance(item_id, str) or not KEBAB.match(item_id):
                errors.append(f"{section} item id must be kebab-case: {item_id}")

    for item in list_items(model, "object_types"):
        data_object = item.get("data_object")
        if data_object not in data_objects:
            errors.append(f"object_type {item.get('id')} references unknown data_object {data_object}")
        state_machine = item.get("state_machine")
        if state_machine not in state_machines:
            errors.append(f"object_type {item.get('id')} references unknown state_machine {state_machine}")
        state_property = item.get("state_property")
        if state_property is None:
            errors.append(
                f"object_type {item.get('id')} must declare state_property "
                f"(its state machine's enum binds to that data_object field)"
            )
        else:
            props = data_object_props.get(data_object, set())
            if not isinstance(state_property, str) or state_property not in props:
                errors.append(
                    f"object_type {item.get('id')} state_property {state_property!r} "
                    f"is not a property of data_object {data_object}"
                )
        for use_case in item.get("use_cases", []):
            if use_case not in use_cases:
                errors.append(f"object_type {item.get('id')} references unknown use case {use_case}")

    for item in list_items(model, "data_objects"):
        name = item.get("name")
        if not isinstance(name, str) or not CS_IDENTIFIER.match(name):
            errors.append(f"data object name must be a C# identifier: {name}")
        properties = item.get("properties")
        if not isinstance(properties, dict) or not properties:
            errors.append(f"data object {name} must define properties")
            continue
        for prop_name, prop_type in properties.items():
            if not isinstance(prop_type, str) or prop_type not in CS_TYPES:
                errors.append(
                    f"data object {name} property {prop_name!r} has unknown type {prop_type!r}; "
                    f"expected one of {sorted(CS_TYPES)}"
                )

    for item in list_items(model, "relationship_types"):
        if item.get("from") not in object_types:
            errors.append(f"relationship {item.get('id')} references unknown from object {item.get('from')}")
        if item.get("to") not in object_types:
            errors.append(f"relationship {item.get('id')} references unknown to object {item.get('to')}")

    object_states = {
        item.get("id"): set(item.get("states", []))
        for item in list_items(model, "object_types")
        if isinstance(item.get("id"), str)
    }
    state_machine_by_object: dict[str, str] = {}
    for item in list_items(model, "state_machines"):
        machine_id = item.get("id")
        object_type = item.get("object_type")
        if object_type not in object_types:
            errors.append(f"state_machine {machine_id} references unknown object_type {object_type}")
            continue
        if object_type in state_machine_by_object:
            errors.append(f"object_type {object_type} has multiple state machines")
        state_machine_by_object[object_type] = str(machine_id)

        states = set(item.get("states", []))
        if not states:
            errors.append(f"state_machine {machine_id} must define states")
        if states != object_states.get(object_type, set()):
            errors.append(f"state_machine {machine_id} states must match object_type {object_type} states")
        # states must be kebab-case and yield unique C# enum members (pascal-cased)
        pascal_states: dict[str, str] = {}
        for state in item.get("states", []):
            if not isinstance(state, str) or not KEBAB.match(state):
                errors.append(f"state_machine {machine_id} state must be kebab-case: {state}")
                continue
            member = pascal(state)
            if member in pascal_states:
                errors.append(
                    f"state_machine {machine_id} states {state!r} and {pascal_states[member]!r} "
                    f"collide as C# enum member {member}"
                )
            pascal_states[member] = state
        if item.get("initial_state") not in states:
            errors.append(f"state_machine {machine_id} initial_state is not a known state")
        for terminal_state in item.get("terminal_states", []):
            if terminal_state not in states:
                errors.append(f"state_machine {machine_id} terminal_state {terminal_state} is not a known state")
        for transition in item.get("transitions", []):
            if not isinstance(transition, dict):
                errors.append(f"state_machine {machine_id} transition must be an object")
                continue
            from_state = transition.get("from")
            to_state = transition.get("to")
            trigger = transition.get("trigger")
            if from_state not in states:
                errors.append(f"state_machine {machine_id} transition from unknown state {from_state}")
            if to_state not in states:
                errors.append(f"state_machine {machine_id} transition to unknown state {to_state}")
            if not isinstance(trigger, str) or not KEBAB.match(trigger):
                errors.append(f"state_machine {machine_id} transition trigger must be kebab-case: {trigger}")

    for item in list_items(model, "workflow_steps"):
        for key in ["reads", "writes"]:
            for object_id in item.get(key, []):
                if object_id not in object_types:
                    errors.append(f"workflow_step {item.get('id')} {key} unknown object {object_id}")

    artifact_ids = {
        artifact.get("id")
        for artifact_group in (model.get("referenced_artifacts") or {}).values()
        for artifact in (artifact_group or [])
        if isinstance(artifact, dict)
    }
    for artifact_group_name, artifact_group in (model.get("referenced_artifacts") or {}).items():
        if not isinstance(artifact_group, list):
            errors.append(f"referenced_artifacts.{artifact_group_name} must be a list")
            continue
        for artifact in artifact_group:
            rel_path = artifact.get("path") if isinstance(artifact, dict) else None
            if not isinstance(rel_path, str):
                errors.append(f"referenced artifact in {artifact_group_name} must define path")
                continue
            if not (model_path.parent / rel_path).exists():
                errors.append(f"referenced artifact does not exist: {rel_path}")

    for item in list_items(model, "scenarios"):
        workflow_ref = item.get("workflow_ref")
        if workflow_ref not in artifact_ids:
            errors.append(f"scenario {item.get('id')} references unknown workflow_ref {workflow_ref}")
        for decision_ref in item.get("decision_refs", []):
            if decision_ref not in artifact_ids:
                errors.append(f"scenario {item.get('id')} references unknown decision_ref {decision_ref}")
        for step_id in item.get("workflow_steps", []):
            if step_id not in workflow_steps:
                errors.append(f"scenario {item.get('id')} references unknown workflow step {step_id}")
        for key in ["input_objects", "output_objects"]:
            for object_id in item.get(key, []):
                if object_id not in object_types:
                    errors.append(f"scenario {item.get('id')} {key} unknown object {object_id}")
        for use_case in item.get("use_cases", []):
            if use_case not in use_cases:
                errors.append(f"scenario {item.get('id')} references unknown use case {use_case}")

    for item in list_items(model, "projections"):
        if item.get("object_type") not in object_types:
            errors.append(f"projection {item.get('id')} references unknown object_type {item.get('object_type')}")

    if not scenarios:
        errors.append("model must define at least one scenario")
    if not relationship_types:
        errors.append("model must define at least one relationship type")
    if not state_machines:
        errors.append("model must define at least one state machine")
    if not projections:
        errors.append("model must define at least one projection")
    return errors


def list_items(model: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = model.get(key, [])
    if not isinstance(value, list):
        raise ModelError(f"{key} must be a list")
    return [item for item in value if isinstance(item, dict)]


def id_set(model: dict[str, Any], key: str, errors: list[str]) -> set[str]:
    seen: set[str] = set()
    for item in list_items(model, key):
        item_id = item.get("id")
        if not isinstance(item_id, str):
            errors.append(f"{key} item is missing string id")
            continue
        if item_id in seen:
            errors.append(f"duplicate {key} id {item_id}")
        seen.add(item_id)
    return seen


def name_set(model: dict[str, Any], key: str, errors: list[str]) -> set[str]:
    seen: set[str] = set()
    for item in list_items(model, key):
        name = item.get("name")
        if not isinstance(name, str):
            errors.append(f"{key} item is missing string name")
            continue
        if name in seen:
            errors.append(f"duplicate {key} name {name}")
        seen.add(name)
    return seen


def pascal(value: str) -> str:
    return "".join(part[:1].upper() + part[1:] for part in re.split(r"[-_\s]+", value) if part)


def camel(value: str) -> str:
    name = pascal(value)
    return name[:1].lower() + name[1:]


def cs_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


CS_TYPES = {
    "string": "string",
    "int": "int",
    "bool": "bool",
    "string[]": "IReadOnlyList<string>",
}


def cs_type(model_type: str) -> str:
    try:
        return CS_TYPES[model_type]
    except (KeyError, TypeError) as exc:
        raise ModelError(
            f"unknown property type {model_type!r}; expected one of {sorted(CS_TYPES)}"
        ) from exc
