import ast
import pathlib
import py_compile
from collections import Counter

ROOT = pathlib.Path(__file__).parent
REPORT = ROOT / 'evidencias' / 'reporte_calidad' / 'analisis_estatico.txt'
PY_FILES = [p for p in ROOT.rglob('*.py') if '.git' not in p.parts and '__pycache__' not in p.parts]


def analyze_file(path: pathlib.Path) -> dict:
    source = path.read_text(encoding='utf-8')
    tree = ast.parse(source)
    functions = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    lines = [line for line in source.splitlines() if line.strip()]
    duplicate_lines = sum(count - 1 for _, count in Counter(lines).items() if count > 1)
    long_functions = 0
    for function in functions:
        end = getattr(function, 'end_lineno', function.lineno)
        if end - function.lineno + 1 > 80:
            long_functions += 1
    return {
        'path': path.relative_to(ROOT),
        'lines': len(lines),
        'functions': len(functions),
        'classes': len(classes),
        'duplicates': duplicate_lines,
        'long_functions': long_functions,
        'todos': source.lower().count('todo')
    }


def main() -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    results = []
    compile_errors = []
    for file_path in PY_FILES:
        try:
            py_compile.compile(str(file_path), doraise=True)
            results.append(analyze_file(file_path))
        except Exception as exc:  # noqa: BLE001 - reporte simple para clase
            compile_errors.append((file_path.relative_to(ROOT), str(exc)))

    total_lines = sum(item['lines'] for item in results)
    total_functions = sum(item['functions'] for item in results)
    total_classes = sum(item['classes'] for item in results)
    total_duplicates = sum(item['duplicates'] for item in results)
    total_long_functions = sum(item['long_functions'] for item in results)
    total_todos = sum(item['todos'] for item in results)
    score = 10
    score -= min(2.0, total_duplicates * 0.02)
    score -= min(1.5, total_long_functions * 0.5)
    score -= min(1.0, len(compile_errors) * 0.5)
    score -= min(0.5, total_todos * 0.1)

    lines = [
        'REPORTE DE ANALISIS ESTATICO - FARMABOL',
        'Herramienta: quality_report.py (revision estatica local)',
        '',
        f'Archivos Python revisados: {len(results)}',
        f'Lineas utiles de codigo: {total_lines}',
        f'Funciones detectadas: {total_functions}',
        f'Clases detectadas: {total_classes}',
        f'Lineas duplicadas estimadas: {total_duplicates}',
        f'Funciones largas (>80 lineas): {total_long_functions}',
        f'Comentarios TODO encontrados: {total_todos}',
        f'Errores de compilacion: {len(compile_errors)}',
        f'Puntaje estimado de calidad: {score:.1f}/10',
        '',
        'Detalle por archivo:'
    ]
    for item in results:
        lines.append(
            f"- {item['path']}: {item['lines']} lineas, {item['functions']} funciones, "
            f"{item['classes']} clases, duplicadas {item['duplicates']}"
        )
    if compile_errors:
        lines.append('')
        lines.append('Errores encontrados:')
        for path, error in compile_errors:
            lines.append(f'- {path}: {error}')
    else:
        lines.append('')
        lines.append('Resultado: no se encontraron errores de compilacion en los archivos Python.')
    REPORT.write_text('\n'.join(lines), encoding='utf-8')
    print(REPORT)


if __name__ == '__main__':
    main()
