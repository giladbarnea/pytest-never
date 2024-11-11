# Copy-paste in the root conftest.py

def extract_test_case_info(node_id: str) -> dict:
    originalname, rest = node_id.split('[', 1)
    rest = rest.rstrip(']')
    parts = rest.split(':')
    testcase = parts[0]
    result = {'originalname': originalname, 'testcase': testcase}

    for part in parts[1:]:
        key, value = part.split('=')
        value = value.strip("'").strip('"')
        if value.isdigit():
            value = int(value)
        elif value.lower() == 'false':
            value = False
        elif value.lower() == 'true':
            value = True
        result[key] = value

    return result

def pytest_runtest_makereport(item: Item, call: CallInfo) -> TestReport | None:
    test_passed = call.when == "call" and call.excinfo is None
    if test_passed:
        everpassed: dict = item.config.cache.get("everpassed", {})
        everpassed_info = extract_test_case_info(item.nodeid)
        everpassed_info.update({'duration': int(call.duration), 'start': int(call.start)})
        if item.nodeid not in everpassed:
            everpassed[item.nodeid] = everpassed_info
            item.config.cache.set("everpassed", everpassed)
        return
    test_failed: bool = call.when == "call" and call.excinfo is not None
    if not test_failed:
        return
    everfailed: dict = item.config.cache.get("everfailed", {})
    everfailed_info = extract_test_case_info(item.nodeid)
    everfailed_info.update({'duration': int(call.duration), 'start': int(call.start)})
    if item.nodeid not in everfailed:
        everfailed[item.nodeid] = everfailed_info
        item.config.cache.set("everfailed", everfailed)
    
def pytest_addoption(parser):
    parser.addoption(
        '--never-passed',
        action='store_true',
        dest='never_passed',
        default=False,
        help='Only run tests that have never passed',
    )
    parser.addoption(
        '--never-failed',
        action='store_true',
        dest='never_failed',
        default=False,
        help='Only run tests that have never failed',
    )

def pytest_collection_modifyitems(session: pytest.Session, config: pytest.Config, items: list[pytest.Item]):
    to_delete_inplace: list[pytest.Item] = []
    never_passed = config.getoption("never_passed")
    ever_passed: dict = config.cache.get("everpassed", {})
    if never_passed:
        for item in items:
            if item.nodeid in ever_passed:
                # item.add_marker(pytest.mark.skip(reason="Has passed before"))
                to_delete_inplace.append(item)

    never_failed = config.getoption("never_failed")
    ever_failed: dict = config.cache.get("everfailed", {})
    if never_failed:
        for item in items:
            if item.nodeid in ever_failed:
                # item.add_marker(pytest.mark.skip(reason="Has failed before"))
                to_delete_inplace.append(item)

    if to_delete_inplace:
        config.hook.pytest_deselected(items=to_delete_inplace)
        for item in to_delete_inplace:
            items.remove(item)

