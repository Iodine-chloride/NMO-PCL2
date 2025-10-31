import requests
import json
import os
import shutil
import re
import argparse
import subprocess
import time
from typing import List, Dict
from datetime import datetime
import fitz  # PyMuPDF for PDF processing

def get_news_detail(news_uuid):
    """
    根据新闻UUID获取新闻详情
    """
    base_url = "https://nmo.net.cn:25569/necore"
    url = f"{base_url}/news/detail/{news_uuid}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"请求失败，状态码: {response.status_code}")
            return None
    except Exception as e:
        print(f"请求发生错误: {e}")
        return None

def get_all_magazines() -> List[Dict]:
    """
    获取所有社刊列表（分页获取所有数据）
    """
    base_url = "https://nmo.net.cn:25569/necore"
    all_magazines = []
    page = 1
    page_size = 50
    
    while True:
        try:
            url = f"{base_url}/news/list"
            payload = {
                "target": "magazine",
                "page": page,
                "page_size": page_size,
                "pin": False
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                magazines = data.get("list", [])
                
                if not magazines:
                    break
                
                all_magazines.extend(magazines)
                print(f"获取第 {page} 页社刊，共 {len(magazines)} 条")
                
                if len(magazines) < page_size:
                    break
                    
                page += 1
            else:
                print(f"获取社刊列表失败，状态码: {response.status_code}")
                break
                
        except Exception as e:
            print(f"获取社刊列表时发生错误: {e}")
            break
    
    return all_magazines

def get_local_magazine_uuids(magazine_path: str) -> List[str]:
    """
    获取本地已存储的社刊UUID列表
    """
    uuids = []
    
    if not os.path.exists(magazine_path):
        return uuids
    
    try:
        for item in os.listdir(magazine_path):
            item_path = os.path.join(magazine_path, item)
            if os.path.isdir(item_path):
                uuids.append(item)
    except Exception as e:
        print(f"获取本地UUID列表时发生错误: {e}")
    
    return uuids

def download_pdf_and_convert_to_images(pdf_url: str, uuid_dir: str, uuid: str) -> int:
    """
    下载PDF文件并转换为图片，然后删除PDF文件
    返回图片数量
    """
    try:
        base_url = "https://nmo.net.cn:25569"
        full_pdf_url = base_url + pdf_url
        
        # 下载PDF文件
        response = requests.get(full_pdf_url)
        if response.status_code != 200:
            print(f"下载PDF失败: {pdf_url}")
            return 0
            
        pdf_path = os.path.join(uuid_dir, "document.pdf")
        with open(pdf_path, 'wb') as f:
            f.write(response.content)
        
        # 使用PyMuPDF将PDF转换为图片
        pdf_document = fitz.open(pdf_path)
        image_count = pdf_document.page_count
        
        for page_num in range(image_count):
            page = pdf_document.load_page(page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 提高分辨率
            image_path = os.path.join(uuid_dir, f"{page_num + 1}.png")
            pix.save(image_path)
        
        pdf_document.close()
        
        # 转换完成后删除PDF文件
        try:
            os.remove(pdf_path)
            print(f"PDF文件已删除: {pdf_path}")
        except Exception as e:
            print(f"删除PDF文件失败: {e}")
        
        print(f"PDF转换完成，共 {image_count} 页")
        return image_count
        
    except Exception as e:
        print(f"PDF转换失败: {e}")
        return 0

def generate_xaml_content(uuid: str, image_count: int) -> str:
    """
    生成XAML文件内容
    """
    xaml_parts = []
    
    # 添加图片部分
    for i in range(1, image_count + 1):
        image_url = f"http://127.0.0.1:8000/pages/magazine/{uuid}/{i}.png"
        image_part = f'''        <Image Height="1000" HorizontalAlignment="Center" 
                Source="{image_url}">
        <Image.OpacityMask>
            <ImageBrush ImageSource="{image_url}" />
        </Image.OpacityMask>
        </Image>'''
        xaml_parts.append(image_part)
    
    images_xaml = "\n".join(xaml_parts)
    
    # 完整的XAML内容
    xaml_content = f'''<local:MyCard Margin="0,0,0,15" CanSwap="False">
    <StackPanel Margin="15,10">
{images_xaml}
    </StackPanel>
</local:MyCard>
<local:MyCard Margin="0,0,0,15" CanSwap="False">
    <Grid Margin="10,6">
        <StackPanel VerticalAlignment="Center" Orientation="Horizontal" HorizontalAlignment="Left" Margin="4,8,0,0">
            <Image Height="30" HorizontalAlignment="Center" Margin="-4,-10,0,0"
                    Source="http://127.0.0.1:8000/icons/nmo2024.png">
            <Image.OpacityMask>
                <ImageBrush ImageSource="http://127.0.0.1:8000/icons/nmo2024.png" />
            </Image.OpacityMask>
            </Image>
            <TextBlock HorizontalAlignment="Left" TextWrapping="Wrap" Margin="4,0,0,8" Text="此页面为自动生成" />
        </StackPanel>
        <StackPanel VerticalAlignment="Center" Orientation="Horizontal" HorizontalAlignment="Right" Margin="-4,0,0,0">
            <local:MyIconTextButton HorizontalAlignment="Left" Text="提交反馈" ToolTip="有问题或者建议可以在这里提交哦" EventType="打开网页"
                                    EventData="https://github.com/Iodine-chloride/NMO-PCL2/issues"
                                    LogoScale="1" Logo="M783.716235 284.987722H264.032742c-22.351978 0-40.51296 18.160982-40.51296 39.115961v413.511597c0 22.351978 18.160982 39.115962 40.51296 39.115961h101.980901l61.46794 58.673943 60.070941-58.673943h297.560709c22.351978 0 40.51296-18.160982 40.512961-39.115961V324.103683c-1.396999-22.351978-19.557981-39.115962-41.909959-39.115961zM374.395634 569.975443c-22.351978 0-40.51296-18.160982-40.51296-39.115961 0-22.351978 18.160982-39.115962 40.51296-39.115962 22.351978 0 40.51296 18.160982 40.512961 39.115962-1.396999 20.95498-19.557981 39.115962-40.512961 39.115961z m149.478854 0c-22.351978 0-40.51296-18.160982-40.51296-39.115961 0-22.351978 18.160982-39.115962 40.51296-39.115962s40.51296 18.160982 40.512961 39.115962c0 20.95498-18.160982 39.115962-40.512961 39.115961z m160.654844 0c-22.351978 0-40.51296-18.160982-40.512961-39.115961 0-22.351978 18.160982-39.115962 40.512961-39.115962s40.51296 18.160982 40.51296 39.115962c-1.396999 20.95498-19.557981 39.115962-40.51296 39.115961z"/>
            <local:MyIconTextButton HorizontalAlignment="Left" Text="GitHub仓库" ToolTip="查看页面源码" EventType="打开网页"
                                    EventData="https://github.com/Iodine-chloride/NMO-PCL2"
                                    LogoScale="1" Logo="M512 42.666667A464.64 464.64 0 0 0 42.666667 502.186667 460.373333 460.373333 0 0 0 363.52 938.666667c23.466667 4.266667 32-9.813333 32-22.186667v-78.08c-130.56 27.733333-158.293333-61.44-158.293333-61.44a122.026667 122.026667 0 0 0-52.053334-67.413333c-42.666667-28.16 3.413333-27.733333 3.413334-27.733334a98.56 98.56 0 0 1 71.68 47.36 101.12 101.12 0 0 0 136.533333 37.973334 99.413333 99.413333 0 0 1 29.866667-61.44c-104.106667-11.52-213.333333-50.773333-213.333334-226.986667a177.066667 177.066667 0 0 1 47.36-124.16 161.28 161.28 0 0 1 4.693334-121.173333s39.68-12.373333 128 46.933333a455.68 455.68 0 0 1 234.666666 0c89.6-59.306667 128-46.933333 128-46.933333a161.28 161.28 0 0 1 4.693334 121.173333A177.066667 177.066667 0 0 1 810.666667 477.866667c0 176.64-110.08 215.466667-213.333334 226.986666a106.666667 106.666667 0 0 1 32 85.333334v125.866666c0 14.933333 8.533333 26.88 32 22.186667A460.8 460.8 0 0 0 981.333333 502.186667 464.64 464.64 0 0 0 512 42.666667"/>
        </StackPanel>
</Grid>
</local:MyCard>'''
    
    return xaml_content

def download_magazine_detail(uuid: str, magazine_path: str) -> bool:
    """
    下载社刊详情并保存为JSON文件，同时创建main.xaml和main.json
    """
    try:
        detail = get_news_detail(uuid)
        if detail is None:
            return False
        
        uuid_dir = os.path.join(magazine_path, uuid)
        os.makedirs(uuid_dir, exist_ok=True)
        
        # 保存原始JSON
        json_path = os.path.join(uuid_dir, "origin.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(detail, f, indent=2, ensure_ascii=False)
        
        # 创建main.json
        title = detail['entity']['title']
        main_json_content = {"Title": f"社刊列表  >  {title}"}
        main_json_path = os.path.join(uuid_dir, "main.json")
        with open(main_json_path, 'w', encoding='utf-8') as f:
            json.dump(main_json_content, f, indent=2, ensure_ascii=False)
        
        # 查找PDF文件并转换
        pdf_url = None
        for content_item in detail.get('content', []):
            if content_item.get('type') == 'pdf_file':
                pdf_url = content_item.get('content')
                break
        
        image_count = 0
        if pdf_url:
            print(f"开始处理PDF: {pdf_url}")
            image_count = download_pdf_and_convert_to_images(pdf_url, uuid_dir, uuid)
        
        # 生成并保存XAML文件
        xaml_content = generate_xaml_content(uuid, image_count)
        xaml_path = os.path.join(uuid_dir, "main.xaml")
        with open(xaml_path, 'w', encoding='utf-8') as f:
            f.write(xaml_content)
        
        print(f"社刊 {uuid} 处理完成: {title}, 共 {image_count} 页")
        return True
        
    except Exception as e:
        print(f"下载社刊详情时发生错误 {uuid}: {e}")
        return False

def delete_local_magazine(uuid: str, magazine_path: str) -> bool:
    """
    删除本地存储的社刊文件夹
    """
    try:
        uuid_dir = os.path.join(magazine_path, uuid)
        if os.path.exists(uuid_dir):
            shutil.rmtree(uuid_dir)
            return True
        return False
    except Exception as e:
        print(f"删除本地社刊时发生错误 {uuid}: {e}")
        return False

def load_magazine_details(magazine_path: str) -> List[Dict]:
    """
    加载所有本地社刊的详细信息
    """
    magazines = []
    
    if not os.path.exists(magazine_path):
        return magazines
    
    try:
        for uuid in os.listdir(magazine_path):
            uuid_dir = os.path.join(magazine_path, uuid)
            json_path = os.path.join(uuid_dir, "origin.json")
            
            if os.path.isdir(uuid_dir) and os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 添加UUID信息
                    data['uuid'] = uuid
                    magazines.append(data)
    except Exception as e:
        print(f"加载社刊详情时发生错误: {e}")
    
    return magazines

def generate_xaml_item(magazine: Dict) -> str:
    """
    生成单个社刊的XAML项目
    """
    title = magazine['entity']['title']
    brief = magazine['entity']['brief']
    uuid = magazine['uuid']
    
    # 格式化XAML项目
    xaml_item = f'''        <local:MyListItem Margin="0,2" ToolTip="点击阅读" LogoScale="1.04"
        Logo="http://127.0.0.1:8000/icons/mc/writable_book.webp" Title="{title}" Info="{brief}"
        EventType="打开帮助" EventData="http://127.0.0.1:8000/pages/magazine/{uuid}/main.json" Type="Clickable" />'''
    
    return xaml_item

def update_main_xaml(magazine_path: str):
    """
    更新main.xaml文件，按照时间排序并区分近期和往期社刊
    """
    # 加载所有社刊详情
    magazines = load_magazine_details(magazine_path)
    
    # 按日期排序（从新到旧）
    magazines.sort(key=lambda x: x['entity']['date'], reverse=True)
    
    # 分离近期社刊（最新3个）和往期社刊
    recent_magazines = magazines[:3]
    past_magazines = magazines[3:]
    
    # 生成XAML内容
    recent_xaml = "\n".join([generate_xaml_item(mag) for mag in recent_magazines])
    past_xaml = "\n".join([generate_xaml_item(mag) for mag in past_magazines])
    
    # 读取原始XAML文件
    xaml_path = os.path.join(magazine_path, "main.xaml")
    
    if not os.path.exists(xaml_path):
        print(f"main.xaml文件不存在: {xaml_path}")
        return False
    
    try:
        with open(xaml_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用正则表达式替换近期社刊部分
        recent_pattern = r'<local:MyCard Title="近期社刊"[^>]*>.*?<StackPanel[^>]*>(.*?)</StackPanel>'
        recent_replacement = f'<local:MyCard Title="近期社刊" Margin="0,0,0,15" CanSwap="False" >\n    <StackPanel Margin="15,40,23,15">\n{recent_xaml}\n    </StackPanel>'
        content = re.sub(recent_pattern, recent_replacement, content, flags=re.DOTALL)
        
        # 使用正则表达式替换往期社刊部分
        past_pattern = r'<local:MyCard Title="往期社刊"[^>]*>.*?<StackPanel[^>]*>(.*?)</StackPanel>'
        past_replacement = f'<local:MyCard Title="往期社刊" Margin="0,0,0,15" CanSwap="False" >\n    <StackPanel Margin="15,40,23,15">\n{past_xaml}\n    </StackPanel>'
        content = re.sub(past_pattern, past_replacement, content, flags=re.DOTALL)
        
        # 写回文件
        with open(xaml_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"已更新main.xaml: 近期社刊 {len(recent_magazines)} 个, 往期社刊 {len(past_magazines)} 个")
        return True
        
    except Exception as e:
        print(f"更新main.xaml时发生错误: {e}")
        return False

def sync_magazines():
    """
    同步社刊列表，处理新增和删除的社刊，并更新main.xaml
    """
    base_url = "https://nmo.net.cn:25569/necore"
    local_magazine_path = "dev/pages/magazine"
    
    os.makedirs(local_magazine_path, exist_ok=True)
    
    try:
        # 获取社刊列表
        magazines = get_all_magazines()
        if magazines is None:
            print("获取社刊列表失败")
            return False
        
        # 获取本地已存在的UUID列表
        local_uuids = get_local_magazine_uuids(local_magazine_path)
        
        # 获取远程UUID列表
        remote_uuids = [magazine["id"] for magazine in magazines]
        
        # 处理新增的社刊
        new_uuids = set(remote_uuids) - set(local_uuids)
        for uuid in new_uuids:
            if download_magazine_detail(uuid, local_magazine_path):
                print(f"新增社刊: {uuid}")
            else:
                print(f"下载社刊详情失败: {uuid}")
        
        # 处理删除的社刊
        deleted_uuids = set(local_uuids) - set(remote_uuids)
        for uuid in deleted_uuids:
            if delete_local_magazine(uuid, local_magazine_path):
                print(f"删除社刊: {uuid}")
            else:
                print(f"删除本地社刊失败: {uuid}")
        
        print(f"同步完成: 新增 {len(new_uuids)} 个, 删除 {len(deleted_uuids)} 个")
        
        # 如果有变化，更新main.xaml
        if new_uuids or deleted_uuids:
            update_main_xaml(local_magazine_path)
        
        return True
        
    except Exception as e:
        print(f"同步过程中发生错误: {e}")
        return False

def dev_command():
    """
    dev命令：在dev目录下运行python3 -m http.server -b 0.0.0.0 8000
    """
    print("启动开发服务器...")
    os.chdir("dev")
    try:
        subprocess.run(["python3", "-m", "http.server", "-b", "0.0.0.0", "8000"])
    except KeyboardInterrupt:
        print("\n开发服务器已停止")
    except Exception as e:
        print(f"启动开发服务器时发生错误: {e}")

def run_command():
    """
    run命令：将dev目录下的所有文件（夹）复制到run目录，
    遇到xaml文件则将所有http:127.0.0.1:8000替换为https://cus.nmo.net.cn:25569，
    并且在run目录下运行python3 -m http.server -b 0.0.0.0 8000
    """
    print("准备生产环境...")
    
    # 确保run目录存在
    if os.path.exists("run"):
        shutil.rmtree("run")
    
    # 复制dev目录到run目录
    shutil.copytree("dev", "run")
    
    # 遍历run目录下的所有xaml文件，替换URL
    for root, dirs, files in os.walk("run"):
        for file in files:
            if file.endswith(".xaml"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 替换URL
                    new_content = content.replace(
                        "http://127.0.0.1:8000", 
                        "https://cus.nmo.net.cn:25569"
                    )
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    print(f"已更新: {file_path}")
                except Exception as e:
                    print(f"处理文件 {file_path} 时发生错误: {e}")
    
    print("启动生产服务器...")
    os.chdir("run")
    try:
        subprocess.run(["python3", "-m", "http.server", "-b", "0.0.0.0", "8000"])
    except KeyboardInterrupt:
        print("\n生产服务器已停止")
    except Exception as e:
        print(f"启动生产服务器时发生错误: {e}")

def check_command():
    """
    check命令：相当于运行原来的news.py（同步社刊）
    """
    print("开始同步社刊...")
    success = sync_magazines()
    
    if success:
        print("社刊同步成功完成")
    else:
        print("社刊同步失败")

def main():
    """
    主函数：解析命令行参数并执行相应命令
    """
    parser = argparse.ArgumentParser(description="社刊管理系统")
    parser.add_argument(
        "command", 
        choices=["dev", "run", "check"], 
        help="命令: dev-开发服务器, run-生产服务器, check-同步社刊"
    )
    
    args = parser.parse_args()
    
    if args.command == "dev":
        dev_command()
    elif args.command == "run":
        run_command()
    elif args.command == "check":
        check_command()

# 使用示例
if __name__ == "__main__":
    main()