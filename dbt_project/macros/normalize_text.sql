{% macro normalize_text(text_column) %}
    lower({{ text_column }}) as normalized_text,
    regexp_replace(
        lower({{ text_column }}),
        '[^a-z0-9\s]',
        '',
        'g'
    ) as cleaned_text,
    regexp_replace(
        regexp_replace(
            lower(coalesce({{ text_column }}, '')),
            '\s+',
            ' ',
            'g'
        ),
        '^\s+|\s+$',
        '',
        'g'
    ) as trimmed_text
{% endmacro %}
