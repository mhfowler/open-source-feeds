import os
import time
import math

from PIL import Image


def fullpage_screenshot(driver, file, dpr, log):

    total_width = driver.execute_script("return document.body.offsetWidth")
    total_height = driver.execute_script("return document.body.parentNode.scrollHeight")
    viewport_height = driver.execute_script("return window.innerHeight")

    zone_height = viewport_height - 200
    num_rectangles = total_height / float(zone_height)
    num_loops = int(math.ceil(num_rectangles))
    stitched_image = Image.new('RGB', (total_width*dpr, total_height*dpr))
    for index in range(0, num_loops):
        scrolled_height = index*zone_height
        driver.execute_script("window.scrollTo({0}, {1})".format(0, scrolled_height))
        time.sleep(0.2)
        scroll_y = driver.execute_script("return window.scrollY")
        file_name = "part_{0}.png".format(index)
        driver.get_screenshot_as_file(file_name)
        screenshot = Image.open(file_name)
        # if scrolled down the page, then crop out the blue bar
        offset_h = 0
        if index > 0:
            offset_h = 44*dpr
            screenshot = screenshot.crop((0, offset_h, screenshot.width*dpr, screenshot.height*dpr))
        stitched_image.paste(screenshot, (0, offset_h + (scroll_y)*dpr))
        del screenshot
        os.remove(file_name)

    stitched_image.save(file)
    return True


def crop_and_save(input_path, location, size, output_path, dpr, log):

    padding = 9 * dpr
    im = Image.open(input_path) # uses PIL library to open image in memory

    left = location['x'] - padding
    top = location['y'] - padding
    right = location['x'] + size['width'] + padding
    bottom = location['y'] + size['height'] + padding + 5

    im = im.crop((left, top, right, bottom)) # defines crop points
    im.save(output_path)


def save_post(post, driver, output_path, dpr, log):
    link = post['link']
    driver.get(link)
    time.sleep(2)

    # try to click x elements
    try:
        x_elements = driver.find_elements_by_css_selector('._418x, ._xlt, ._418x')
        if x_elements:
            x = x_elements[0]
            x.click()
            time.sleep(2)
    except:
        pass

    # try to click the body
    try:
        x_elements = driver.find_elements_by_css_selector('._n9')
        if x_elements:
            x = x_elements[0]
            x.click()
            time.sleep(1)
    except:
        pass


    elements = driver.find_elements_by_css_selector('._1w_m')
    if elements:
        element = elements[0]
        location = {'y': element.location['y'] * dpr, 'x': element.location['x'] * dpr}
        size = {'width': (element.size['width'] * dpr), 'height': element.size['height'] * dpr}
        temp_path = 'screenshot.png'
        fullpage_screenshot(driver=driver, file=temp_path, dpr=dpr, log=log)
        crop_and_save(input_path=temp_path, location=location, size=size, output_path=output_path, dpr=dpr, log=log)
