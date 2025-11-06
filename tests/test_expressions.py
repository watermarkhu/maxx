"""Tests for the expressions module."""

from unittest.mock import Mock

from maxx.expressions import MATHWORKS_DOC_URL, MATLAB_BUILTINS, Expr


class TestExpr:
    """Test class for Expr."""

    def test_iterate(self):
        """Test that iterate yields decoded node text."""
        mock_node1 = Mock()
        mock_node1.text = b"test"
        mock_node2 = Mock()
        mock_node2.text = b"value"

        expr = Expr(nodes=[mock_node1, mock_node2], encoding="utf-8")  # type: ignore[arg-type]
        result = list(expr.iterate())

        assert result == ["test", "value"]

    def test_iterate_with_none_text(self):
        """Test that iterate skips nodes with None text."""
        mock_node1 = Mock()
        mock_node1.text = b"test"
        mock_node2 = Mock()
        mock_node2.text = None

        expr = Expr(nodes=[mock_node1, mock_node2], encoding="utf-8")  # type: ignore[arg-type]
        result = list(expr.iterate())

        assert result == ["test"]

    def test_str(self):
        """Test string representation of Expr."""
        mock_node1 = Mock()
        mock_node1.text = b"hello"
        mock_node2 = Mock()
        mock_node2.text = b" "
        mock_node3 = Mock()
        mock_node3.text = b"world"

        expr = Expr(nodes=[mock_node1, mock_node2, mock_node3], encoding="utf-8")  # type: ignore[arg-type]

        assert str(expr) == "hello world"

    def test_iter(self):
        """Test that __iter__ yields values."""
        mock_node1 = Mock()
        mock_node1.text = b"first"
        mock_node2 = Mock()
        mock_node2.text = b"second"

        expr = Expr(nodes=[mock_node1, mock_node2], encoding="utf-8")  # type: ignore[arg-type]
        result = list(iter(expr))

        assert result == ["first", "second"]

    def test_doc_with_builtin(self):
        """Test doc property with a MATLAB builtin."""
        # Find a builtin from the actual MATLAB_BUILTINS dict
        if MATLAB_BUILTINS:
            builtin_name = next(iter(MATLAB_BUILTINS.keys()))
            builtin_url = MATLAB_BUILTINS[builtin_name]

            mock_node = Mock()
            mock_node.text = builtin_name.encode("utf-8")

            expr = Expr(nodes=[mock_node], encoding="utf-8")  # type: ignore[arg-type]
            expected_doc = f"{MATHWORKS_DOC_URL}/{builtin_url}"

            assert expr.doc == expected_doc

    def test_doc_without_builtin(self):
        """Test doc property with non-builtin."""
        mock_node = Mock()
        mock_node.text = b"not_a_builtin_function_xyz123"

        expr = Expr(nodes=[mock_node], encoding="utf-8")  # type: ignore[arg-type]

        assert expr.doc == ""

    def test_doc_with_multiple_nodes(self):
        """Test doc property with multiple nodes."""
        # Use a builtin if available
        if MATLAB_BUILTINS:
            builtin_name = next(iter(MATLAB_BUILTINS.keys()))
            builtin_url = MATLAB_BUILTINS[builtin_name]

            mock_node1 = Mock()
            mock_node1.text = b"prefix"
            mock_node2 = Mock()
            mock_node2.text = builtin_name.encode("utf-8")

            expr = Expr(nodes=[mock_node1, mock_node2], encoding="utf-8")  # type: ignore[arg-type]
            expected_doc = f"{MATHWORKS_DOC_URL}/{builtin_url}"

            # Should find the builtin in the second node
            assert expr.doc == expected_doc
