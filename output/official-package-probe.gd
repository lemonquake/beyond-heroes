extends SceneTree

func _initialize() -> void:
    _check.call_deferred()

func _check() -> void:
    await create_timer(1.0).timeout
    assert(FileAccess.file_exists('res://server/official.cfg'))
    assert(FileAccess.file_exists('res://server/official_ca.crt'))
    assert(not FileAccess.file_exists('res://server/server.json'))
    assert(not FileAccess.file_exists('res://server/server.key'))
    for path in ['autoload/official_service', 'autoload/save_system', 'net/net', 'ui/menu/server_menu', 'ui/menu/main_menu']:
        assert(FileAccess.file_exists('res://src/%s.gdc' % path))
    assert(root.get_node('Net').MAX_PLAYERS == 12)
    assert(root.get_node('SaveSystem').scope == 'legacy')
    print('OFFICIAL PACKAGE: verified compiled server client, realm menu and public TLS identity')
    quit(0)
