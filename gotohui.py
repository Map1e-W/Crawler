from datetime import datetime, timedelta, timezone

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import os
from PIL import Image

def create_city_folder(parent_folder, city):
    """创建以城市为名的文件夹"""
    folder_path = os.path.join(parent_folder, city)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    return folder_path

def take_full_page_screenshot(driver, save_path):
    """分段截图并拼接为完整的长截图"""
    try:
        # 获取页面的总高度和宽度
        total_height = driver.execute_script("return document.body.scrollHeight")
        total_width = driver.execute_script("return document.body.scrollWidth")

        # 设置浏览器窗口的大小
        # driver.set_window_size(total_width, total_height)

        # 分段截图
        screenshots = []
        scroll_height = driver.execute_script("return window.innerHeight")
        offset = 0

        while offset < total_height:
            # 滚动页面并截图
            driver.execute_script(f"window.scrollTo(0, {offset});")
            time.sleep(0.5)  # 等待页面渲染
            screenshot_path = f"temp_{offset}.png"
            driver.save_screenshot(screenshot_path)
            screenshots.append(screenshot_path)
            offset += scroll_height

        # 拼接截图
        images = [Image.open(screenshot) for screenshot in screenshots]
        total_width = max(image.width for image in images)
        total_height = sum(image.height for image in images)

        combined_image = Image.new("RGB", (total_width, total_height))
        y_offset = 0
        for image in images:
            combined_image.paste(image, (0, y_offset))
            y_offset += image.height
            image.close()

        # 保存拼接后的长截图
        combined_image.save(save_path)
        print(f"长截图已保存到文件: {save_path}")

        # 删除临时截图文件
        for screenshot in screenshots:
            os.remove(screenshot)

    except Exception as e:
        print(f"截取长截图时出错: {e}")

def get_data_for_city(driver, city, data_type):
    """获取指定城市和数据类型的数据"""
    try:
        # --- 第一步：搜索目标数据 ---
        print(f"正在搜索 {city} 的 {data_type}...")

        # 等待搜索框加载完成
        time.sleep(2)  # 等待页面加载
        search_box = driver.find_element(By.ID, "searchkey")

        # 输入关键词并按下回车
        search_box.clear()
        search_box.send_keys(f"{city} {data_type}")
        search_box.send_keys(Keys.RETURN)

        # --- 第二步：定位数据链接 ---
        print(f"正在定位 {city} 的 {data_type} 数据链接...")

        # 等待中间列表加载完成
        time.sleep(2)  # 等待页面加载
        rows = driver.find_elements(By.CSS_SELECTOR, ".ntable tbody tr")

        # 动态生成目标链接文本（城市+数据类型）
        if data_type == "出生人口":
            target_text = f"{city}出生人数"
        elif data_type == "死亡人口":
            target_text = f"{city}死亡人数"
        elif data_type == "自然增长率":
            target_text = f"{city}自然增长率"
        else:
            print(f"未知的数据类型: {data_type}")
            return None

        found_link = None

        # 遍历所有数据条目
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 2:  # 至少有两列：标题和链接
                link_element = cells[1].find_element(By.TAG_NAME, "a")
                link_text = link_element.text.strip()
                if (all(char in link_text for char in target_text)
                    and (link_text.endswith(target_text[-1]))
                    and "区" not in link_text
                    and "镇" not in link_text
                    and "县" not in link_text
                    and link_text.count("市") == 1):
                # if target_text in link_text:
                    found_link = link_element.get_attribute("href")
                    print(f"找到目标链接: {found_link}")
                    link_element.click()  # 点击链接进入详情页面
                    break

        if not found_link:
            print(f"未找到 {city} 的 {data_type} 数据链接！")
            return None

        # --- 第三步：切换到新页面并关闭旧页面 ---
        print(f"正在切换到新页面并关闭旧页面...")

        # 获取所有窗口句柄
        window_handles = driver.window_handles

        # 切换到新打开的页面
        driver.switch_to.window(window_handles[1])

        # 关闭旧页面
        driver.switch_to.window(window_handles[0])
        driver.close()
        driver.switch_to.window(window_handles[1])

        # --- 第四步：截取数据页面的长截图 ---
        print(f"正在截取数据页面的长截图...")

        # 等待数据页面加载完成
        time.sleep(2)  # 增加等待时间

        # 创建以城市为名的文件夹
        folder_path = create_city_folder(time_folder_path, city)
        screenshot_path = os.path.join(folder_path, f"{data_type}_full_page_screenshot.png")

        # 截取整个页面的长截图
        take_full_page_screenshot(driver, screenshot_path)
        return 1

    except Exception as e:
        print(f"获取 {city} 的 {data_type} 数据时出错: {e}")
        return None

def main():
    # 初始化 WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--incognito")  # 无痕模式
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()  # 最大化窗口
    driver.get("https://population.gotohui.com/")  # 初始页面

    # 目标城市和数据类型
    city_types = ["石家庄市", "唐山市", "秦皇岛市", "邯郸市", "邢台市" , "邢台市", "张家口市"]
    # city = "深圳市"
    data_types = ["出生人口", "死亡人口", "自然增长率"]

    # 依次搜索并截图
    for city in city_types:
        for data_type in data_types:
            result = get_data_for_city(driver, city, data_type)
            if result is not None:
                print(f"{city} 的 {data_type} 数据页面长截图已完成！")
            else:
                print(f"{city} 的 {data_type} 数据页面长截图失败！")

            # 返回初始页面以便下一次搜索
            driver.get("https://population.gotohui.com/")
            # time.sleep(2)

    # 关闭浏览器
    driver.quit()

if __name__ == "__main__":
    utc_now = datetime.now(timezone.utc)
    beijing_timezone = timezone(timedelta(hours=8))
    beijing_time = utc_now.replace(tzinfo=timezone.utc).astimezone(beijing_timezone)
    time_folder_name = beijing_time.strftime("%Y-%m-%d_%H-%M-%S")
    time_folder_path = os.path.join(os.getcwd(), time_folder_name)

    if not os.path.exists(time_folder_path):
        os.makedirs(time_folder_path)
    print(f"已创建时间文件夹: {time_folder_path}")
    main()