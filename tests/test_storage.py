"""``installed.db``: its shape, and every question and change the kit makes of it."""

import sqlite3

import pytest
from conftest import INSTALLED_AT, build_component, build_installed

from claude_kit.components import ComponentKind
from claude_kit.components.installed_component import ComponentConfig, ConfigStatus
from claude_kit.storage import (
    SCHEMA_VERSION,
    add_component,
    ensure_schema,
    find_components_by_name,
    get_installed_components,
    get_schema_version,
    remove_components,
    set_component_config,
    set_component_enabled,
)
from claude_kit.storage.schema import COMPONENT_COLUMNS


def test_ensure_schema_stamps_the_version(connection):
    assert get_schema_version(connection) == SCHEMA_VERSION


def test_ensure_schema_twice_changes_nothing(connection):
    add_component(connection, build_installed(build_component()))
    ensure_schema(connection)
    assert len(get_installed_components(connection)) == 1


def test_component_columns_match_the_table(connection):
    in_table = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(installed_components)")
    }
    assert in_table == {"id", *COMPONENT_COLUMNS}


def test_the_check_constraint_accepts_every_kind(connection):
    for kind in ComponentKind:
        add_component(connection, build_installed(build_component(kind=kind)))
    assert len(get_installed_components(connection)) == len(ComponentKind)


def test_a_kind_outside_the_enum_is_refused(connection):
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO installed_components (kind, name, tag, source, installed_at)"
            " VALUES ('hook', 'x', '', 'genie', ?)",
            (INSTALLED_AT,),
        )


def test_a_component_round_trips_every_stored_field(connection):
    installed = build_installed(
        build_component(
            source="skillhub",
            description="Reviews code carefully",
            version="1.2.0",
            tag="global",
        )
    )
    add_component(connection, installed)
    read = get_installed_components(connection)[0]
    stored = installed.component
    assert read.component.kind is stored.kind
    assert read.component.name == stored.name
    assert read.component.source == stored.source
    assert read.component.description == stored.description
    assert read.component.version == stored.version
    assert read.component.tag == stored.tag
    assert read.installed_at == installed.installed_at
    assert read.enabled is True
    assert read.config.status is ConfigStatus.NONE
    assert read.config.keys == {}


def test_popularity_does_not_survive_the_database(connection):
    """The table has no ``popularity`` column: it is what a source reports at search
    time, not a fact about an install. Delete this test the day one is added."""
    add_component(connection, build_installed(build_component(popularity=128)))
    assert get_installed_components(connection)[0].component.popularity is None


def test_config_keys_round_trip(connection):
    keys = {"GENIE_TOKEN": True, "GENIE_ORG": False}
    add_component(
        connection,
        build_installed(
            build_component(),
            config=ComponentConfig(status=ConfigStatus.DONE, keys=keys),
        ),
    )
    read = get_installed_components(connection)[0]
    assert read.config.status is ConfigStatus.DONE
    assert read.config.keys == keys


def test_the_same_name_and_tag_twice_is_refused(connection):
    installed = build_installed(build_component())
    add_component(connection, installed)
    with pytest.raises(sqlite3.IntegrityError):
        add_component(connection, installed)


def test_replace_leaves_one_row(connection):
    installed = build_installed(build_component())
    add_component(connection, installed)
    add_component(connection, installed, replace=True)
    assert len(get_installed_components(connection)) == 1


def test_the_same_name_under_another_tag_is_a_second_row(connection):
    add_component(connection, build_installed(build_component()))
    add_component(connection, build_installed(build_component(tag="acme")))
    assert len(get_installed_components(connection)) == 2


def test_get_installed_components_filters_by_kind(connection):
    add_component(connection, build_installed(build_component(ComponentKind.SKILL)))
    add_component(connection, build_installed(build_component(ComponentKind.AGENT)))
    found = get_installed_components(connection, ComponentKind.AGENT)
    assert [entry.component.kind for entry in found] == [ComponentKind.AGENT]


def test_find_components_by_name_narrows_on_the_tag(connection):
    add_component(connection, build_installed(build_component()))
    add_component(connection, build_installed(build_component(tag="acme")))
    both = find_components_by_name(connection, ComponentKind.SKILL, "code-reviewer")
    one = find_components_by_name(
        connection, ComponentKind.SKILL, "code-reviewer", "acme"
    )
    assert len(both) == 2
    assert [entry.component.tag for entry in one] == ["acme"]


def test_find_components_by_name_answers_empty_for_a_miss(connection):
    assert find_components_by_name(connection, ComponentKind.SKILL, "nothing") == []


def test_remove_components_reports_what_it_deleted(connection):
    component = build_component()
    add_component(connection, build_installed(component))
    assert remove_components(connection, component.kind, component.name) == 1
    assert get_installed_components(connection) == []


def test_removing_a_component_cascades_to_its_config_keys(connection):
    component = build_component()
    add_component(
        connection,
        build_installed(
            component,
            config=ComponentConfig(status=ConfigStatus.DONE, keys={"TOKEN": True}),
        ),
    )
    remove_components(connection, component.kind, component.name)
    left = connection.execute("SELECT COUNT(*) FROM component_config_keys").fetchone()
    assert left[0] == 0


def test_set_component_config_replaces_the_keys(connection):
    component = build_component()
    add_component(connection, build_installed(component))
    changed = set_component_config(
        connection,
        component.kind,
        component.name,
        component.tag,
        ComponentConfig(status=ConfigStatus.PENDING, keys={"TOKEN": False}),
    )
    read = get_installed_components(connection)[0]
    assert changed == 1
    assert read.config.status is ConfigStatus.PENDING
    assert read.config.keys == {"TOKEN": False}


def test_set_component_enabled_flips_it(connection):
    component = build_component()
    add_component(connection, build_installed(component))
    changed = set_component_enabled(
        connection, component.kind, component.name, component.tag, False
    )
    assert changed == 1
    assert get_installed_components(connection)[0].enabled is False
