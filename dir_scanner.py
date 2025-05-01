import os
import sys
import time
import argparse
from pathlib import Path
import requests
from concurrent.futures import ThreadPoolExecutor
import urllib3
import json
import csv
import random
import datetime

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 作者信息
__author__ = "Amonologue"
__version__ = "1.1.0"
__description__ = "一个功能强大的目录扫描工具，支持本地和Web目录扫描"

def print_banner():
    """打印工具横幅和作者信息"""
    banner = f"""
    ██████╗ ██╗██████╗     ███████╗ ██████╗ █████╗ ███╗   ██╗███╗   ██╗███████╗██████╗ 
    ██╔══██╗██║██╔══██╗    ██╔════╝██╔════╝██╔══██╗████╗  ██║████╗  ██║██╔════╝██╔══██╗
    ██║  ██║██║██████╔╝    ███████╗██║     ███████║██╔██╗ ██║██╔██╗ ██║█████╗  ██████╔╝
    ██║  ██║██║██╔══██╗    ╚════██║██║     ██╔══██║██║╚██╗██║██║╚██╗██║██╔══╝  ██╔══██╗
    ██████╔╝██║██║  ██║    ███████║╚██████╗██║  ██║██║ ╚████║██║ ╚████║███████╗██║  ██║
    ╚═════╝ ╚═╝╚═╝  ╚═╝    ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝
                                                                                        
    ╔═════════════════════════════════════════════════════════════════════════════╗
    ║  作者: {__author__}                                                       ║
    ║  版本: {__version__}                                                      ║
    ║  启动时间: {time.strftime('%Y-%m-%d %H:%M:%S')}                           ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

# 将不专业的中文注释改为：
def get_file_size_str(size_in_bytes):
    """将字节大小转换为人类可读的格式"""  # 1
    if size_in_bytes < 0:
        return "未知大小"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} PB"

def scan_directory(directory, file_extension=None, recursive=True, output_file=None):
    """
    扫描目录并打印文件信息
    
    参数:
        directory (str): 要扫描的目录路径
        file_extension (str): 可选，按文件扩展名筛选
        recursive (bool): 是否递归扫描子目录
        output_file (str): 可选，输出结果的文件路径
    """
    start_time = time.time()
    directory = Path(directory)
    
    if not directory.exists():
        print(f"错误: 目录 '{directory}' 不存在")
        return
    
    if not directory.is_dir():
        print(f"错误: '{directory}' 不是一个目录")
        return
    
    output_lines = []
    output_lines.append(f"扫描目录: {directory.absolute()}")
    output_lines.append(f"扫描时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    if file_extension:
        output_lines.append(f"文件过滤: {file_extension}")
    output_lines.append(f"递归扫描: {'是' if recursive else '否'}")
    output_lines.append("-" * 80)
    output_lines.append(f"{'文件名':<50} {'大小':<10} {'修改时间':<20} {'类型':<10}")
    output_lines.append("-" * 80)
    
    total_files = 0
    total_dirs = 0
    total_size = 0
    
    # 定义遍历函数
    def process_directory(current_dir, indent=""):
        nonlocal total_files, total_dirs, total_size
        
        try:
            # 获取目录内容并排序
            items = sorted(current_dir.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            
            for item in items:
                if item.is_dir():
                    total_dirs += 1
                    rel_path = item.relative_to(directory)
                    output_lines.append(f"{indent}[{rel_path}]")
                    
                    # 递归处理子目录
                    if recursive:
                        process_directory(item, indent + "  ")
                
                elif item.is_file():
                    # 检查文件扩展名
                    if file_extension and not item.name.lower().endswith(file_extension.lower()):
                        continue
                    
                    total_files += 1
                    file_size = item.stat().st_size
                    total_size += file_size
                    mod_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(item.stat().st_mtime))
                    file_type = item.suffix[1:] if item.suffix else "无扩展名"
                    
                    rel_path = item.relative_to(directory)
                    size_str = get_file_size_str(file_size)
                    
                    output_lines.append(f"{indent}{rel_path!s:<50} {size_str:<10} {mod_time:<20} {file_type:<10}")
        
        except PermissionError:
            output_lines.append(f"{indent}[访问被拒绝]")
        except Exception as e:
            output_lines.append(f"{indent}[扫描错误: {str(e)}]")
    
    # 开始扫描
    print(f"正在扫描目录: {directory.absolute()}")
    process_directory(directory)
    
    # 添加统计信息
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    output_lines.append("-" * 80)
    output_lines.append(f"总计: {total_files} 个文件, {total_dirs} 个目录")
    output_lines.append(f"总大小: {get_file_size_str(total_size)}")
    output_lines.append(f"扫描用时: {elapsed_time:.2f} 秒")
    
    # 输出结果
    for line in output_lines:
        print(line)
    
    # 如果指定了输出文件，则写入文件
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for line in output_lines:
                    f.write(line + '\n')
            print(f"\n结果已保存到: {output_file}")
        except Exception as e:
            print(f"写入输出文件时出错: {str(e)}")

def load_dictionary(dict_file):
    """从字典文件加载路径"""
    paths = []
    try:
        with open(dict_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    paths.append(line)
        return paths
    except Exception as e:
        print(f"加载字典文件 {dict_file} 时出错: {str(e)}")
        return []

def get_random_user_agent():
    """返回随机用户代理"""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36 OPR/78.0.4093.184",
    ]
    return random.choice(user_agents)

def scan_url(url, path, timeout=5, verify=False, headers=None, proxy=None):
    """扫描单个URL路径"""
    full_url = url.rstrip('/') + '/' + path.lstrip('/')
    try:
        if headers is None:
            headers = {
                "User-Agent": get_random_user_agent(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Connection": "keep-alive",
            }
        
        proxies = None
        if proxy:
            proxies = {
                'http': proxy,
                'https': proxy
            }
        
        response = requests.get(full_url, timeout=timeout, verify=verify, allow_redirects=False, headers=headers, proxies=proxies)
        status = response.status_code
        if 200 <= status < 400:
            content_length = len(response.content)
            content_type = response.headers.get('Content-Type', '未知')
            
            return {
                'url': full_url,
                'status': status,
                'length': content_length,
                'size': get_file_size_str(content_length),
                'content_type': content_type,
                'path': path
            }
        return None
    except requests.exceptions.ConnectionError:
        return None
    except requests.exceptions.Timeout:
        return None
    except Exception as e:
        return None

def export_results(results, output_file, format='txt', base_url=None, dict_file=None):
    """导出扫描结果到文件"""
    if format == 'txt':
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"扫描URL: {base_url}\n")
            f.write(f"扫描时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"字典文件: {dict_file}\n")
            f.write("-" * 80 + "\n")
            f.write(f"{'URL':<60} {'状态码':<10} {'大小':<10} {'内容类型':<20}\n")
            f.write("-" * 80 + "\n")
            for result in results:
                f.write(f"{result['url']:<60} {result['status']:<10} {result['size']:<10} {result.get('content_type', '未知'):<20}\n")
            f.write("-" * 80 + "\n")
            f.write(f"扫描完成: 发现 {len(results)} 个有效路径\n")
    elif format == 'json':
        with open(output_file, 'w', encoding='utf-8') as f:
            json_data = {
                'scan_info': {
                    'url': base_url,
                    'time': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'dict_file': dict_file,
                    'found_count': len(results)
                },
                'results': results
            }
            json.dump(json_data, f, indent=4, ensure_ascii=False)
    elif format == 'csv':
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['URL', '状态码', '大小(字节)', '大小', '内容类型', '路径'])
            for result in results:
                writer.writerow([
                    result['url'], 
                    result['status'], 
                    result['length'], 
                    result['size'],
                    result.get('content_type', '未知'),
                    result.get('path', '')
                ])
    else:
        print(f"不支持的导出格式: {format}")
        return False
    
    return True

def web_scan(base_url, dict_file, threads=10, timeout=5, delay=0, status_codes=None, 
             min_size=None, max_size=None, output_file=None, format='txt', proxy=None):
    """使用字典文件扫描Web目录"""
    start_time = time.time()
    paths = load_dictionary(dict_file)
    if not paths:
        print(f"字典文件 {dict_file} 为空或无法加载")
        return
    
    print(f"从字典文件 {dict_file} 加载了 {len(paths)} 个路径")
    print(f"开始扫描 {base_url}")
    if proxy:
        print(f"使用代理: {proxy}")
    print("-" * 80)
    print(f"{'URL':<60} {'状态码':<10} {'大小':<10} {'内容类型':<20}")
    print("-" * 80)
    
    results = []
    found_count = 0
    total_paths = len(paths)
    completed = 0
    
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {}
        for path in paths:
            # 添加随机延迟
            if delay > 0:
                time.sleep(random.uniform(0, delay))
            futures[executor.submit(scan_url, base_url, path, timeout, verify=False, proxy=proxy)] = path
        
        for future in futures:
            result = future.result()
            completed += 1
            
            # 显示进度条
            progress = int(50 * completed / total_paths)
            elapsed = time.time() - start_time
            eta = (elapsed / completed) * (total_paths - completed) if completed > 0 else 0
            
            status_line = f"\r进度: [{'#' * progress}{' ' * (50 - progress)}] {completed}/{total_paths} ({completed/total_paths*100:.1f}%) "
            status_line += f"已用时: {int(elapsed//60)}分{int(elapsed%60)}秒 "
            status_line += f"预计剩余: {int(eta//60)}分{int(eta%60)}秒"
            
            sys.stdout.write(status_line)
            sys.stdout.flush()
            
            if result:
                # 根据状态码过滤
                if status_codes and result['status'] not in status_codes:
                    continue
                
                # 根据大小过滤
                if min_size is not None and result['length'] < min_size:
                    continue
                if max_size is not None and result['length'] > max_size:
                    continue
                
                found_count += 1
                print(f"\n{result['url']:<60} {result['status']:<10} {result['size']:<10} {result.get('content_type', '未知'):<20}")
                results.append(result)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    print("\n" + "-" * 80)
    print(f"扫描完成: 发现 {found_count} 个有效路径，共测试 {len(paths)} 个路径")
    print(f"扫描用时: {elapsed_time:.2f} 秒，平均速度: {len(paths)/elapsed_time:.2f} 请求/秒")
    
    if output_file and results:
        try:
            export_results(results, output_file, format, base_url, dict_file)
            print(f"\n结果已保存到: {output_file}")
        except Exception as e:
            print(f"写入输出文件时出错: {str(e)}")
    
    return results

def main():
    # 显示作者信息
    print_banner()
    
    parser = argparse.ArgumentParser(description=__description__)
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # 本地目录扫描子命令
    local_parser = subparsers.add_parser('local', help='扫描本地目录')
    local_parser.add_argument('directory', nargs='?', default='.', help='要扫描的目录路径 (默认为当前目录)')
    local_parser.add_argument('-e', '--extension', help='按文件扩展名筛选 (例如: .txt, .py)')
    local_parser.add_argument('-nr', '--no-recursive', action='store_true', help='不递归扫描子目录')
    local_parser.add_argument('-o', '--output', help='将结果保存到指定文件')
    
    # Web目录扫描子命令
    web_parser = subparsers.add_parser('web', help='扫描Web目录')
    web_parser.add_argument('url', help='要扫描的基础URL (例如: http://example.com)')
    web_parser.add_argument('-d', '--dict', required=True, help='字典文件路径')
    web_parser.add_argument('-t', '--threads', type=int, default=10, help='线程数 (默认: 10)')
    web_parser.add_argument('--timeout', type=int, default=5, help='请求超时时间(秒) (默认: 5)')
    web_parser.add_argument('--delay', type=float, default=0, help='请求间隔延迟(秒) (默认: 0)')
    web_parser.add_argument('--status', type=int, nargs='+', help='只显示指定状态码的结果 (例如: 200 301 302)')
    web_parser.add_argument('--min-size', type=int, help='最小响应大小(字节)')
    web_parser.add_argument('--max-size', type=int, help='最大响应大小(字节)')
    web_parser.add_argument('--format', choices=['txt', 'json', 'csv'], default='txt', help='导出格式 (默认: txt)')
    web_parser.add_argument('-o', '--output', help='将结果保存到指定文件')
    web_parser.add_argument('--proxy', help='使用代理 (例如: http://127.0.0.1:8080)')
    web_parser.add_argument('-H', '--header', action='append', help='自定义请求头 (例如: "Cookie: name=value")')
    
    args = parser.parse_args()
    
    # 如果没有提供命令，显示帮助信息
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'local':
            scan_directory(
                args.directory,
                file_extension=args.extension,
                recursive=not args.no_recursive,
                output_file=args.output
            )
        elif args.command == 'web':
            # 处理自定义请求头
            headers = None
            if args.header:
                headers = {}
                for header in args.header:
                    if ':' in header:
                        key, value = header.split(':', 1)
                        headers[key.strip()] = value.strip()
            
            # 如果没有指定输出文件，自动生成一个
            output_file = args.output
            if not output_file and args.url:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                domain = args.url.replace('http://', '').replace('https://', '').split('/')[0]
                output_file = f"scan_{domain}_{timestamp}.{args.format}"
            
            web_scan(
                args.url,
                args.dict,
                threads=args.threads,
                timeout=args.timeout,
                delay=args.delay,
                status_codes=args.status,
                min_size=args.min_size,
                max_size=args.max_size,
                output_file=output_file,
                format=args.format,
                proxy=args.proxy
            )
    except KeyboardInterrupt:
        print("\n\n扫描被用户中断")
    except Exception as e:
        print(f"\n扫描过程中出错: {str(e)}")

if __name__ == "__main__":
    main()