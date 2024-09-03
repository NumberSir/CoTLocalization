import esprima
import json

def analyze_js_file(file_path):
    with open(file_path, 'r',encoding="utf-8") as file:
        js_code = file.read()

    # 解析JavaScript代码
    ast = esprima.parseScript(js_code, {'loc': True, 'range': True})

    # 遍历AST
    def traverse(node, parent=None):
        if isinstance(node, dict):
            node_type = node.get('type')
            if node_type == 'VariableDeclaration':
                for declaration in node['declarations']:
                    var_name = declaration['id']['name']
                    var_type = get_variable_type(declaration['init'])
                    # print(f"Variable: {var_name}, Type: {var_type}")
                    if var_type == 'Object':
                        print(f"Object structure: {json.dumps(declaration['init'], indent=2)}")
                    # print(f"Position: {node['loc']['start']['line']}:{node['loc']['start']['column']}")
            elif node_type == 'ObjectExpression':
                print(f"Object found: {json.dumps(node, indent=2)}")
                print(f"Position: {node['loc']['start']['line']}:{node['loc']['start']['column']}")

            for key, value in node.items():
                if key not in ['loc', 'range']:
                    traverse(value, node)
        elif isinstance(node, list):
            for item in node:
                traverse(item, parent)

    def get_variable_type(node):
        if node is None:
            return 'Undefined'
        node_type = node.get('type')
        if node_type == 'Literal':
            return type(node['value']).__name__
        elif node_type == 'ObjectExpression':
            return 'Object'
        elif node_type == 'ArrayExpression':
            return 'Array'
        elif node_type == 'FunctionExpression':
            return 'Function'
        else:
            return node_type

    traverse(ast.toDict())

# 使用函数
analyze_js_file('database_clothes.js')
