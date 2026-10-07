import pytest

from scripts.import_test_labels_cp24_r1 import expand_truncated


def test_expand_restores_full_unit_text():
    units = ['Frameworks such as LangChain, LlamaIndex, Hugging Face, vLLM, or similar', 'Python']
    text = 'The CV supports LLM and Frameworks such as LangChain, LlamaIndex, Hugging Fa…, but no.'
    out, changes = expand_truncated(text, units)
    assert out == ('The CV supports LLM and Frameworks such as LangChain, LlamaIndex, Hugging Face, '
                   'vLLM, or similar, but no.')
    assert len(changes) == 1


def test_expand_handles_sentence_end():
    units = ['Hands-on experience with a modern deep-learning framework']
    out, _ = expand_truncated('Missing in Hands-on experience with a modern deep-learning fram….', units)
    assert out == 'Missing in Hands-on experience with a modern deep-learning framework.'


def test_expand_refuses_without_unique_unit():
    with pytest.raises(SystemExit):
        expand_truncated('Supports Something that is not in A at all…, ok.', ['Other unit text here long'])
