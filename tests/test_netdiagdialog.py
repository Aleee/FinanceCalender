from gui.netdiagdialog import NetDiagDialog


def test_start_disabled_options_follow_token(qapp):
    without_token = NetDiagDialog("", "app:/")
    assert not without_token.chb_send.isEnabled()
    assert not without_token.chb_send.isChecked()
    with_token = NetDiagDialog("abc", "app:/")
    assert with_token.chb_send.isChecked()


def test_report_ready_enables_show_button(qapp, tmp_path):
    dialog = NetDiagDialog("abc", "app:/")
    dialog.on_report_ready(str(tmp_path / "netdiag.zip"))
    dialog.on_finished()
    assert dialog.pb_folder.isEnabled()
    assert dialog.pb_start.isEnabled()
    assert not dialog.pb_stop.isEnabled()
