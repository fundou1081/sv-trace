#!/usr/bin/env python3
"""
Design Evaluator - 综合设计评估工具
Usage: python -m src.apps.evaluate <file.sv> [--module <name>]
"""
import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.parse.parser import SVParser
from src.debug.design_evaluator import DesignEvaluator


def main():
    parser = argparse.ArgumentParser(description='SystemVerilog Design Evaluator')
    parser.add_argument('file', help='SV file to evaluate')
    parser.add_argument('--module', '-m', help='Specific module to evaluate')
    parser.add_argument('--format', '-f', choices=['text', 'mermaid', 'json'], 
                        default='text', help='Output format')
    parser.add_argument('--output', '-o', help='Output file')
    
    args = parser.parse_args()
    
    # 解析文件
    sv_parser = SVParser()
    sv_parser.parse_file(args.file)
    
    # 评估
    evaluator = DesignEvaluator(sv_parser)
    evaluator.evaluate(args.module)
    
    # 输出
    if args.format == 'text':
        output = evaluator.get_full_report()
    elif args.format == 'mermaid':
        output = evaluator.get_mermaid_graph()
    elif args.format == 'json':
        import json
        # 收集可序列化的结果
        dep = evaluator.results.get('dependency', {})
        stats = dep.get('stats', {})
        comp = dep.get('complexity_score', {})
        quality = evaluator.results.get('complexity', {}).get('quality_report', {})
        
        output = json.dumps({
            'dependency': {
                'stats': stats,
                'complexity_score': comp
            },
            'complexity': quality
        }, indent=2)
    
    # 写入文件或 stdout
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"Output written to: {args.output}")
    else:
        print(output)


if __name__ == '__main__':
    main()
