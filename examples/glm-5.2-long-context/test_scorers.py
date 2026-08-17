from scorers import ASTSemanticMatch, SubstringMatch


def test_function_count_requires_numeric_equality():
    row = {"question_type": "FC"}
    assert ASTSemanticMatch(row, "There are 12 functions.", "12")["score"] == 1
    assert ASTSemanticMatch(row, "There are 13 functions.", "12")["score"] == 0


def test_base_classes_are_order_independent():
    row = {"question_type": "BC"}
    score = ASTSemanticMatch(row, "It inherits Mapping and Generic.", "Generic, Mapping")
    assert score["score"] == 1


def test_paths_allow_cpython_prefixes():
    row = {"question_type": "CL"}
    assert ASTSemanticMatch(row, "Lib/email/message.py", "email/message.py")["score"] == 1


def test_short_substrings_require_token_boundaries():
    assert SubstringMatch({}, "It returns int64.", "int")["score"] == 0
    assert SubstringMatch({}, "It returns int.", "int")["score"] == 1
