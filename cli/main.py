#!/usr/bin/env python3
"""
sv-trace - SystemVerilog 追踪工具
"""
import argparse
import sys
import os
import glob

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from parse import SVParser
from trace.driver import DriverTracer
from trace.load import LoadTracer
from trace.datapath import DataPathAnalyzer
from trace.controlflow import ControlFlowTracer
from trace.visualize import visualize_datapath, visualize_controlflow
from lint.linter import SVLinter
from debug.assistant import DebugAssistant
from debug.analyzers.clock_domain import ClockDomainAnalyzer
from debug.analyzers.cdc import CDCAnalyzer
from debug.reports.generator import ReportGenerator

def analyze_signal(args):
    parser = SVParser()
    if os.path.isdir(args.file):
        for sv_file in glob.glob(os.path.join(args.file, '*.sv')):
            parser.parse_file(sv_file)
    else:
        parser.parse_file(args.file)
    
    analyzer = DataPathAnalyzer(parser)
    if args.module:
        dp = analyzer.analyze_module()
    else:
        dp = analyzer.analyze(args.signal)
    print(dp.visualize())

def list_signals(args):
    parser = SVParser()
    parser.parse_file(args.file)
    
    all_signals = set()
    for tree in parser.trees.values():
        if not tree or not hasattr(tree, 'root'):
            continue
        root = tree.root
        members = getattr(root, 'members', None)
        if not members:
            continue
        for i in range(len(members)):
            member = members[i]
            if 'ModuleDeclaration' not in str(type(member)):
                continue
            mod_members = getattr(member, 'members', None)
            if not mod_members:
                continue
            for j in range(len(mod_members)):
                mm = mod_members[j]
                if 'DataDeclaration' not in str(type(mm)):
                    continue
                declarators = getattr(mm, 'declarators', None)
                if declarators:
                    try:
                        for decl in declarators:
                            if hasattr(decl, 'name'):
                                name = decl.name.value if hasattr(decl.name, 'value') else str(decl.name)
                                all_signals.add(name)
                    except TypeError:
                        pass
    
    print(f"Found {len(all_signals)} signals:")
    for sig in sorted(all_signals):
        print(f"  {sig}")

def find_drivers(args):
    parser = SVParser()
    parser.parse_file(args.file)
    tracer = DriverTracer(parser)
    drivers = tracer.find_driver(args.signal)
    print(f"Drivers for '{args.signal}':")
    if not drivers:
        print("  (none)")
    for d in drivers:
        print(f"  [{d.driver_kind.name}] {d.source_expr.strip()}")

def find_loads(args):
    parser = SVParser()
    parser.parse_file(args.file)
    tracer = LoadTracer(parser)
    loads = tracer.find_load(args.signal)
    print(f"Loads of '{args.signal}':")
    if not loads:
        print("  (none)")
    for l in loads:
        print(f"  {l.signal_name}")

def controlflow(args):
    parser = SVParser()
    parser.parse_file(args.file)
    tracer = ControlFlowTracer(parser)
    flow = tracer.find_control_dependencies(args.signal)
    print(flow.visualize())

def visualize(args):
    parser = SVParser()
    parser.parse_file(args.file)
    
    if args.type == "datapath":
        dot = visualize_datapath(parser, args.signal)
    elif args.type == "controlflow":
        dot = visualize_controlflow(parser, args.signal)
    else:
        print("Error: invalid type")
        return
    
    if args.output:
        output = args.output
        if not output.endswith('.dot'):
            output += '.dot'
        with open(output, 'w') as f:
            f.write(dot)
        print(f"DOT saved to: {output}")
    else:
        print(dot)

def lint(args):
    parser = SVParser()
    parser.parse_file(args.file)
    
    linter = SVLinter(parser)
    
    if args.check == "all":
        report = linter.run_all()
    elif args.check == "unused":
        report = linter.check_unused_signals()
    elif args.check == "multi":
        report = linter.check_multiple_drivers()
    else:
        print(f"Unknown check: {args.check}")
        return
    
    print(report.visualize())

def diagnose(args):
    """诊断信号问题"""
    parser = SVParser()
    parser.parse_file(args.file)
    
    assistant = DebugAssistant(parser)
    result = assistant.ask(args.question)
    
    print(result.content)
    if result.details:
        for d in result.details:
            print(f"  {d}")
    if result.suggestions:
        print("Suggestions:")
        for s in result.suggestions:
            print(f"  - {s}")

def clock_domain(args):
    """时钟域分析"""
    parser = SVParser()
    parser.parse_file(args.file)
    
    analyzer = ClockDomainAnalyzer(parser)
    
    print("=== Clock Domain Analysis ===")
    
    domains = analyzer.get_all_domains()
    print(f"\nClock Domains: {len(domains)}")
    for d in domains:
        signals = analyzer.get_signals_in_domain(d)
        print(f"  {d}: {len(signals)} signals")
    
    registers = analyzer.get_all_registers()
    print(f"\nRegisters: {len(registers)}")
    for sig, info in list(registers.items())[:10]:
        print(f"  {sig}: clock={info.clock}, edge={info.clock_edge}")

def report(args):
    """生成报告"""
    parser = SVParser()
    parser.parse_file(args.file)
    
    generator = ReportGenerator(parser)
    report = generator.generate_report()
    
    if ns.format == "html":
        output = generator.to_html(report)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"HTML report saved to: {args.output}")
        else:
            print(output)
    elif ns.format == "markdown":
        output = generator.to_markdown(report)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"Markdown report saved to: {args.output}")
        else:
            print(output)

def dependency(args):
    """模块依赖分析"""
    from parse import SVParser
    from debug.dependency import ModuleDependencyAnalyzer
    
    parser = SVParser()
    if os.path.isdir(args.file):
        for sv_file in glob.glob(os.path.join(args.file, '*.sv')):
            parser.parse_file(sv_file)
    else:
        parser.parse_file(args.file)
    
    analyzer = ModuleDependencyAnalyzer(parser)
    graph = analyzer.analyze()
    
    if args.format == 'json':
        import json
        data = {
            'modules': {name: {
                'depends_on': mod.depends_on,
                'depended_by': mod.depended_by,
                'instances': [i.instance_name for i in mod.instances]
            } for name, mod in graph.modules.items()},
            'root_modules': graph.root_modules,
            'leaf_modules': graph.leaf_modules,
            'cycles': graph.cycles
        }
        print(json.dumps(data, indent=2))
    else:
        print("=" * 60)
        print("Module Dependency Analysis")
        print("=" * 60)
        
        if graph.cycles:
            print("\n⚠️  Cycles detected: " + str(len(graph.cycles)))
            for cycle in graph.cycles:
                print("  " + " -> ".join(cycle))
        
        print("\nRoot modules: " + str(graph.root_modules))
        print("Leaf modules: " + str(graph.leaf_modules))
        
        print("\nModules (" + str(len(graph.modules)) + "):")
        for name in sorted(graph.modules.keys()):
            mod = graph.modules[name]
            inst_count = len(mod.instances)
            deps = mod.depends_on
            print("  " + name + ": " + str(inst_count) + " instances, depends_on=" + str(deps))



def ask(args):
    """自然语言查询"""
    parser = SVParser()
    parser.parse_file(args.file)
    
    assistant = DebugAssistant(parser)
    result = assistant.ask(args.question)
    
    print(f"Intent: {result.intent.value}")
    print(f"Signal: {result.signal}")
    print(f"\n{result.content}")
    if result.details:
        print("\nDetails:")
        for d in result.details:
            print(f"  - {d}")

def cdc(args):
    """CDC 分析"""
    parser = SVParser()
    parser.parse_file(args.file)
    
    analyzer = CDCAnalyzer(parser)
    report = analyzer.analyze()
    
    print("=== CDC Analysis ===")
    print(f"\nStatistics:")
    for k, v in report.statistics.items():
        print(f"  {k}: {v}")
    
    if report.issues:
        print(f"\nIssues Found ({len(report.issues)}):")
        for issue in report.issues:
            print(f"  [{issue.severity}] {issue.signal}")
            print(f"    {issue.from_domain} -> {issue.to_domain}")
            print(f"    Mitigation: {issue.mitigation}")
    else:
        print(f"\nNo CDC issues found!")


def dependency(args):
    """模块依赖分析"""
    from parse import SVParser
    from debug.dependency import ModuleDependencyAnalyzer
    
    parser = SVParser()
    if os.path.isdir(args.file):
        for sv_file in glob.glob(os.path.join(args.file, '*.sv')):
            parser.parse_file(sv_file)
    else:
        parser.parse_file(args.file)
    
    analyzer = ModuleDependencyAnalyzer(parser)
    graph = analyzer.analyze()
    
    if args.format == 'json':
        import json
        data = {
            'modules': {name: {
                'depends_on': mod.depends_on,
                'depended_by': mod.depended_by,
                'instances': [i.instance_name for i in mod.instances]
            } for name, mod in graph.modules.items()},
            'root_modules': graph.root_modules,
            'leaf_modules': graph.leaf_modules,
            'cycles': graph.cycles
        }
        print(json.dumps(data, indent=2))
    else:
        print("=" * 60)
        print("Module Dependency Analysis")
        print("=" * 60)
        
        if graph.cycles:
            print("\n⚠️  Cycles detected: " + str(len(graph.cycles)))
            for cycle in graph.cycles:
                print("  " + " -> ".join(cycle))
        
        print("\nRoot modules: " + str(graph.root_modules))
        print("Leaf modules: " + str(graph.leaf_modules))
        
        print("\nModules (" + str(len(graph.modules)) + "):")
        for name in sorted(graph.modules.keys()):
            mod = graph.modules[name]
            inst_count = len(mod.instances)
            deps = mod.depends_on
            print("  " + name + ": " + str(inst_count) + " instances, depends_on=" + str(deps))


def main():
    import sys as _sys
    parser = argparse.ArgumentParser(
        description='sv-trace: SystemVerilog 追踪工具',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command')
    
    # analyze
    p = subparsers.add_parser('analyze', help='分析信号数据流')
    
    # dependency - 模块依赖分析
    p = subparsers.add_parser('dependency', help='模块依赖分析')
    p.add_argument('file', help='输入文件或目录')
    p.add_argument('--format', choices=['text', 'json'], default='text')
    p.set_defaults(func=dependency)
    
    # signals
    p = subparsers.add_parser('signals', help='列出所有信号')
    p.add_argument('file')
    p.set_defaults(func=list_signals)
    
    # drivers
    p = subparsers.add_parser('drivers', help='查找驱动')
    p.add_argument('file')
    p.add_argument('-s', '--signal', required=True)
    p.set_defaults(func=find_drivers)
    
    # loads
    p = subparsers.add_parser('loads', help='查找负载')
    p.add_argument('file')
    p.add_argument('-s', '--signal', required=True)
    p.set_defaults(func=find_loads)
    
    # controlflow
    p = subparsers.add_parser('controlflow', help='分析控制流')
    p.add_argument('file')
    p.add_argument('-s', '--signal', required=True)
    p.set_defaults(func=controlflow)
    
    # visualize
    p = subparsers.add_parser('visualize', help='生成流程图')
    p.add_argument('file')
    p.add_argument('-s', '--signal', required=True)
    p.add_argument('-t', '--type', choices=['datapath', 'controlflow'], default='datapath')
    p.add_argument('-o', '--output')
    p.set_defaults(func=visualize)
    
    # diagnose
    p = subparsers.add_parser('diagnose', help='诊断信号问题')
    p.add_argument('file')
    p.add_argument('-q', '--question', required=True, help='问题描述')
    p.set_defaults(func=diagnose)
    
    # clock-domain
    p = subparsers.add_parser('clock-domain', help='时钟域分析')
    p.add_argument('file')
    p.set_defaults(func=clock_domain)
    
    # report
    p = subparsers.add_parser('report', help='生成调试报告')
    p.add_argument('file')
    p.add_argument('-o', '--output', help='输出文件')
    p.add_argument('-f', '--format', choices=['html', 'markdown'], default='html')
    p.set_defaults(func=report)
    
    # ask
    p = subparsers.add_parser('ask', help='自然语言查询')
    p.add_argument('file')
    p.add_argument('-q', '--question', required=True, help='查询内容')
    p.set_defaults(func=ask)
    
    # lint
    p = subparsers.add_parser('lint', help='Lint 静态检查')
    p.add_argument('file')
    p.add_argument('-c', '--check', choices=['all', 'unused', 'multi'], default='all')
    p.set_defaults(func=lint)
    

    # iospec - IO规范提取
    p = subparsers.add_parser('iospec', help='Extract module IO specification')
    p.add_argument('--file', '-f', required=True, help='Input SystemVerilog file')
    p.add_argument('--module', '-m', help='Module name')
    p.add_argument('--format', choices=['text', 'json'], default='text')
    p.set_defaults(func=lambda ns: iospec_handler(ns))
    
    # fsm - 状态机提取
    p = subparsers.add_parser('fsm', help='状态机提取')
    p.add_argument('file', help='输入文件')
    p.add_argument('--format', choices=['text', 'json'], default='text')
    p.set_defaults(func=fsm_handler)

    # Parse and execute
    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)


def fsm_handler(ns):
    """状态机提取"""
    from parse import SVParser
    from debug.fsm import FSMExtractor
    
    parser = SVParser()
    parser.parse_file(ns.file)
    
    extractor = FSMExtractor(parser)
    fsm_list = extractor.extract()
    
    if ns.format == 'json':
        import json
        data = {
            'fsm_count': len(fsm_list),
            'fsms': [{
                'name': f.name,
                'state_var': f.state_var,
                'states': [s.name for s in f.states],
                'reset_state': f.reset_state,
                'transitions': {
                    s.name: [{'cond': c, 'next': n} for c, n in s.transitions]
                    for s in f.states
                }
            } for f in fsm_list]
        }
        print(json.dumps(data, indent=2))
    else:
        print("=" * 60)
        print("FSM Extraction Results")
        print("=" * 60)
        print()
        if not fsm_list:
            print("No FSMs found")
        else:
            for fsm in fsm_list:
                print(fsm.visualize())
                print()


def iospec_handler(ns):
    from parse import SVParser
    from debug.iospec import IOSpecExtractor
    
    parser = SVParser()
    parser.parse_file(ns.file)
    
    extractor = IOSpecExtractor(parser)
    spec = extractor.extract(ns.module)
    
    if ns.format == 'json':
        import json
        data = {
            'module': spec.module_name,
            'ports': [{'name': p.name, 'direction': p.direction.value, 'width': p.width, 'category': p.category.value} for p in spec.ports],
            'data_flows': spec.data_flows
        }
        print(json.dumps(data, indent=2))
    else:
        print(extractor.generate_flow_diagram(spec))


if __name__ == '__main__':
    main()
