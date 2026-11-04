from tests.formparse import admin_form_data


def test_parser_reads_inputs_selects_and_textareas() -> None:
    html = """
    <form>
      <input type="hidden" name="csrf" value="token">
      <input type="checkbox" name="skip" value="1">
      <input type="checkbox" name="keep" value="1" checked>
      <input type="text" name="title" value="Ada">
      <select name="author">
        <option value="1">One</option>
        <option value="2" selected>Two</option>
      </select>
      <textarea name="notes">hello</textarea>
      <input type="submit" name="_save" value="Save">
    </form>
    """
    data = admin_form_data(html)
    assert data["csrf"] == "token"
    assert "skip" not in data
    assert data["keep"] == "1"
    assert data["title"] == "Ada"
    assert data["author"] == "2"
    assert data["notes"] == "hello"
    assert "_save" not in data
