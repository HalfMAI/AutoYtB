import io
import time
import traceback

import requests
import numpy
import utitls
from selenium import webdriver
from PIL import Image, ImageChops
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as Wait
from selenium.webdriver.support import expected_conditions as Expect
from selenium.webdriver.common.action_chains import ActionChains


def login(username, password):
    browser = None
    try:
        if utitls.configJson().get("driver_type", "chrome") == "firefox":
            firefox_option = webdriver.FirefoxOptions()
            firefox_option.headless = True
            browser = webdriver.Firefox(firefox_options=firefox_option)
        else:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.headless = True
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-sync')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-translate')
            browser = webdriver.Chrome(chrome_options=chrome_options)

        browser.get('https://passport.bilibili.com/login')
        Wait(browser, 60).until(
            Expect.visibility_of_element_located((By.CLASS_NAME, "gt_slider"))
        )
        username_input = browser.find_element_by_id("login-username")
        username_input.send_keys(username)
        password_input = browser.find_element_by_id("login-passwd")
        password_input.send_keys(password)

        retry_times = 0
        max_retry_times = utitls.configJson().get("login_retry_times", 3)
        while retry_times < max_retry_times:
            do_captcha(browser)
            Wait(browser, 20).until(
                Expect.visibility_of_element_located((By.CLASS_NAME, "gt_info_tip"))
            )
            if Expect.visibility_of_element_located((By.CLASS_NAME, "gt_success"))  \
                    or Expect.visibility_of_element_located((By.ID, "banner_link")):
                break
            retry_times += 1
            Wait(browser, 10).until(
                Expect.invisibility_of_element_located((By.CLASS_NAME, "gt_fail"))
            )
            time.sleep(1)
        if retry_times >= max_retry_times:
            return ""


        #check is login Success
        Wait(browser, 60).until(
            Expect.visibility_of_element_located((By.ID, "banner_link"))
        )
        browser.get('https://link.bilibili.com/p/center/index')
        Wait(browser, 10).until(
            Expect.visibility_of_element_located((By.CLASS_NAME, "user"))
        )
        time.sleep(5)   #wait for the cookies
        cookies = browser.get_cookies()
        cookies_str_array = []
        for cookie in cookies:
            cookies_str_array.append(cookie["name"]+"="+cookie["value"])
        browser.quit()
        return ";".join(cookies_str_array)
    except Exception as e:
        utitls.myLogger(traceback.format_exc())
        utitls.myLogger(str(e))
        if browser is not None:
            browser.quit()
        return ""


def do_captcha(browser):
    offset = get_captcha_offset(browser)
    drag_button(browser, offset)


def get_captcha_offset(browser):
    slice_image_url = browser.find_element_by_class_name("gt_slice").value_of_css_property("background-image").split('"')[1]
    slice_image = Image.open(io.BytesIO(requests.get(slice_image_url).content))
    slice_offset = find_not_transparent_point_offset(slice_image)
    cut_image_url = browser.find_element_by_class_name("gt_cut_bg_slice").value_of_css_property("background-image").split('"')[1]
    cut_image = Image.open(io.BytesIO(requests.get(cut_image_url).content))
    source_cut_image = Image.new('RGB', (260, 116))
    cut_image_elements = browser.find_elements_by_class_name("gt_cut_bg_slice")
    index = 0
    for cut_image_element in cut_image_elements:
        background_position = cut_image_element.value_of_css_property("background-position")
        offset = convert_background_position_to_offset(background_position)
        source_cut_image.paste(cut_image.crop(offset), convert_index_to_offset(index))
        index += 1
    full_image_url = browser.find_element_by_class_name("gt_cut_fullbg_slice").value_of_css_property("background-image").split('"')[1]
    full_image = Image.open(io.BytesIO(requests.get(full_image_url).content))
    source_full_image = Image.new('RGB', (260, 116))
    full_image_elements = browser.find_elements_by_class_name("gt_cut_fullbg_slice")
    index = 0
    for full_image_element in full_image_elements:
        background_position = full_image_element.value_of_css_property("background-position")
        offset = convert_background_position_to_offset(background_position)
        source_full_image.paste(full_image.crop(offset), convert_index_to_offset(index))
        index += 1
    offset = find_different_point_offset(source_cut_image, source_full_image)
    return offset - slice_offset


def convert_background_position_to_offset(background_position):
    background_position_parts = background_position.replace(' ', '').split("px")
    x = -int(background_position_parts[0])
    y = -int(background_position_parts[1])
    return x, y, x+10, y+58


def convert_index_to_offset(index):
    if index >= 26:
        return (index - 26) * 10, 58, (index - 25) * 10, 116
    else:
        return index * 10, 0, (index + 1) * 10, 58


def find_not_transparent_point_offset(image):
    width, height = image.size
    offset_array = []
    for h in range(height):
        for w in range(width):
            r, g, b, alpha = image.getpixel((w, h))
            if alpha > 150:
                offset_array.append(w)
                break
    offset = min(offset_array)
    return offset


def find_different_point_offset(image1, image2):
    diff_image = ImageChops.difference(image1, image2)
    width, height = diff_image.size
    offset_array = []
    for h in range(height):
        for w in range(width):
            r, g, b = diff_image.getpixel((w, h))
            min_rgb = min(r, g, b)
            max_rgb = max(r, g, b)
            if max_rgb - min_rgb > 40 or max_rgb > 50:
                offset_array.append(w)
                break
    offset = min(offset_array)
    return offset


def drag_button(browser, offset):
    button = browser.find_element_by_class_name("gt_slider_knob")
    time_long = round(numpy.random.uniform(3.0, 5.0), 1)
    ActionChains(browser).click_and_hold(button).perform()
    current_offset = 0
    pause_time = round(numpy.random.uniform(0.5, 1.5), 1)
    real_drag_time_long = time_long - pause_time
    for s in numpy.arange(0, real_drag_time_long, 0.1):
        new_offset = round(ease_out_back(s/real_drag_time_long) * offset)
        if pause_time > 0:
            ActionChains(browser).pause(pause_time)
        ActionChains(browser).move_by_offset(new_offset - current_offset, 0).perform()
        current_offset = new_offset
        pause_time = 0
    ActionChains(browser).move_by_offset(offset - current_offset, 0).perform()
    ActionChains(browser).pause(0.5).release().perform()


def ease_out_back(x):
    return 1 + 2.70158 * pow(x - 1, 3) + 1.70158 * pow(x - 1, 2)
