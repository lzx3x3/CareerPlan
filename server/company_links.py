"""
招聘平台跳转链接生成器
根据公司/机构名称，生成各招聘平台的搜索链接
支持公务员/事业单位按省份筛选
"""
import urllib.parse

# 城市 → 省份映射表（用于事业单位招聘按省份筛选）
CITY_TO_PROVINCE = {
    '北京': '北京', '上海': '上海', '天津': '天津', '重庆': '重庆',
    '广州': '广东', '深圳': '广东', '东莞': '广东', '佛山': '广东', '珠海': '广东',
    '惠州': '广东', '中山': '广东', '汕头': '广东', '湛江': '广东',
    '南京': '江苏', '苏州': '江苏', '无锡': '江苏', '常州': '江苏', '南通': '江苏',
    '扬州': '江苏', '徐州': '江苏', '连云港': '江苏', '盐城': '江苏',
    '杭州': '浙江', '宁波': '浙江', '温州': '浙江', '嘉兴': '浙江', '绍兴': '浙江',
    '金华': '浙江', '台州': '浙江', '湖州': '浙江',
    '成都': '四川', '绵阳': '四川', '德阳': '四川', '宜宾': '四川',
    '武汉': '湖北', '宜昌': '湖北', '襄阳': '湖北',
    '长沙': '湖南', '株洲': '湖南', '湘潭': '湖南', '衡阳': '湖南',
    '郑州': '河南', '洛阳': '河南', '开封': '河南', '新乡': '河南',
    '济南': '山东', '青岛': '山东', '烟台': '山东', '潍坊': '山东', '威海': '山东',
    '合肥': '安徽', '芜湖': '安徽', '蚌埠': '安徽',
    '福州': '福建', '厦门': '福建', '泉州': '福建', '漳州': '福建',
    '石家庄': '河北', '保定': '河北', '唐山': '河北', '邯郸': '河北',
    '太原': '山西', '大同': '山西', '运城': '山西',
    '沈阳': '辽宁', '大连': '辽宁', '鞍山': '辽宁',
    '长春': '吉林', '吉林市': '吉林',
    '哈尔滨': '黑龙江', '大庆': '黑龙江',
    '西安': '陕西', '咸阳': '陕西', '宝鸡': '陕西',
    '兰州': '甘肃', '天水': '甘肃',
    '昆明': '云南', '大理': '云南', '曲靖': '云南',
    '贵阳': '贵州', '遵义': '贵州',
    '南宁': '广西', '桂林': '广西', '柳州': '广西',
    '海口': '海南', '三亚': '海南',
    '呼和浩特': '内蒙古', '包头': '内蒙古', '鄂尔多斯': '内蒙古',
    '银川': '宁夏',
    '西宁': '青海',
    '乌鲁木齐': '新疆', '昌吉': '新疆',
    '拉萨': '西藏',
    '南昌': '江西', '九江': '江西', '赣州': '江西',
}

# 省份 → 省份简称（用于 URL 拼接）
PROVINCE_SHORT = {
    '北京': 'bj', '上海': 'sh', '天津': 'tj', '重庆': 'cq',
    '广东': 'gd', '江苏': 'js', '浙江': 'zj', '四川': 'sc',
    '湖北': 'hb', '湖南': 'hn', '河南': 'ha', '山东': 'sd',
    '安徽': 'ah', '福建': 'fj', '河北': 'he', '山西': 'sx',
    '辽宁': 'ln', '吉林': 'jl', '黑龙江': 'hl', '陕西': 'sn',
    '甘肃': 'gs', '云南': 'yn', '贵州': 'gz', '广西': 'gx',
    '海南': 'hi', '内蒙古': 'nm', '宁夏': 'nx', '青海': 'qh',
    '新疆': 'xj', '西藏': 'xz', '江西': 'jx',
}


def get_company_links(company_name: str, city: str = '') -> list:
    """
    根据公司名称生成招聘平台链接
    city: 用户期望就业城市，用于事业单位按省份筛选
    返回 [{name, url, icon, desc}] 列表
    """
    if not company_name or not company_name.strip():
        return []

    company = company_name.strip()
    encoded = urllib.parse.quote(company)

    # 解析省份
    province = CITY_TO_PROVINCE.get(city, '')
    if not province and city:
        # 城市名可能直接就是省份名
        if city in PROVINCE_SHORT:
            province = city

    # ===== 公务员/事业单位：使用专门的考公平台 =====
    gwy_keywords = ['公务员', '事业单位', '政府机构', '政府机关', '机关单位', '体制内', '编制', '局']
    is_gwy = any(kw in company for kw in gwy_keywords)

    if is_gwy:
        # 复用 get_gwy_links 获取考公链接
        return get_gwy_links(city)

    # ===== 普通企业：使用常规招聘平台 =====
    links = [
        {
            'name': '实习僧',
            'url': f'https://www.shixiseng.com/interns?keyword={encoded}',
            'icon': '🎓',
            'desc': '实习岗位'
        },
        {
            'name': 'Boss直聘',
            'url': f'https://www.zhipin.com/web/geek/job?query={encoded}',
            'icon': '💼',
            'desc': '社招/实习'
        },
        {
            'name': '智联招聘',
            'url': f'https://www.zhaopin.com/sou/?keyword={encoded}',
            'icon': '📋',
            'desc': '综合招聘'
        },
        {
            'name': '前程无忧',
            'url': f'https://we.51job.com/pc/search/job?keyword={encoded}',
            'icon': '🔍',
            'desc': '综合招聘'
        },
        {
            'name': '牛客网',
            'url': f'https://www.nowcoder.com/search?type=post&query={encoded}',
            'icon': '🧑‍💻',
            'desc': '技术岗/校招'
        },
    ]

    # 如果是研究所/科研机构，额外添加科研相关平台
    research_keywords = ['研究所', '研究院', '科研', '科学院', '实验室', '大学', '高校']
    if any(kw in company for kw in research_keywords):
        links.extend([
            {
                'name': '高校人才网',
                'url': f'https://www.gaoxiaojob.com/search?keyword={encoded}',
                'icon': '🏛️',
                'desc': '高校/科研'
            },
            {
                'name': '科学网',
                'url': f'https://talent.sciencenet.cn/search/?keyword={encoded}',
                'icon': '🔬',
                'desc': '科研招聘'
            },
        ])

    return links




def get_gwy_links(city: str = '') -> list:
    """
    获取公务员/事业单位考试报名信息链接（不依赖公司名）
    根据用户期望就业城市自动定位省份
    返回 [{name, url, icon, desc}] 列表
    """
    # 解析省份
    province = CITY_TO_PROVINCE.get(city, '')
    if not province and city:
        if city in PROVINCE_SHORT:
            province = city

    province_desc = f'（{province}）' if province else ''
    province_pinyin = PROVINCE_SHORT.get(province, '')

    links = []

    # 1. 国家公务员考试（官方）
    links.append({
        'name': '国家公务员考试',
        'url': 'http://bm.scs.gov.cn/pp/gkweb/core/web/ui/business/person/person_home.html',
        'icon': '🏛️',
        'desc': '国考公告/报名/职位查询（官方）'
    })

    # 2. 省考 - 中公教育（按省份）
    if province_pinyin:
        links.append({
            'name': f'省考职位查询{province_desc}',
            'url': f'https://www.offcn.com/{province_pinyin}gwy/',
            'icon': '📋',
            'desc': f'{province}公务员考试资讯'
        })
    else:
        links.append({
            'name': '省考职位查询',
            'url': 'https://www.offcn.com/gjgwy/',
            'icon': '📋',
            'desc': '各省公务员考试资讯'
        })

    # 3. 事业单位（按省份）
    if province:
        links.append({
            'name': f'{province}事业单位招聘',
            'url': f'https://sydw.huatu.com/{province_pinyin}/' if province_pinyin else 'https://sydw.huatu.com/zhaopin/',
            'icon': '🏢',
            'desc': f'{province}事业单位招聘信息'
        })

    # 4. 公考雷达
    links.append({
        'name': '公考雷达',
        'url': 'https://www.gongkaoleida.com/',
        'icon': '📡',
        'desc': '公职考试选岗工具'
    })

    # 5. 粉笔教育
    links.append({
        'name': '粉笔教育',
        'url': 'https://fenbi.com/',
        'icon': '✏️',
        'desc': '考公/事业单位公告与备考'
    })

    # 6. 事业单位考试网
    links.append({
        'name': '事业单位考试网',
        'url': 'https://www.shiyebian.net/xinxi/',
        'icon': '📖',
        'desc': '事业单位招聘信息汇总'
    })

    return links


def parse_companies_from_ai_plan(ai_plan_text: str) -> list:
    """
    从 AI 生成的职业规划文本中提取公司/机构名称
    返回去重后的公司名列表
    """
    if not ai_plan_text:
        return []

    # 常见的公司/机构后缀
    company_suffixes = [
        '有限公司', '股份公司', '集团', '科技', '技术',
        '研究所', '研究院', '科学院', '实验室',
        '大学', '学院', '高校',
        '银行', '证券', '基金',
        '腾讯', '阿里', '百度', '字节', '美团', '京东', '华为', '小米',
        '比亚迪', '大疆', '网易', '滴滴', '快手', '拼多多', '蚂蚁',
        '微软', '谷歌', '苹果', '亚马逊', 'Meta',
        '中科院', '清华', '北大', '复旦', '交大', '浙大', '南大',
        '中科大', '哈工大', '北航', '北理', '华科', '武大',
    ]

    # 简单的名称提取逻辑
    found_companies = set()

    # 按行分析，寻找包含公司特征的文本
    import re

    lines = ai_plan_text.split('\n')
    for line in lines:
        # 匹配可能的机构名称模式
        # 模式1: 中文+后缀
        for suffix in company_suffixes:
            if suffix in line:
                # 尝试提取完整名称
                pattern = rf'([\u4e00-\u9fa5A-Za-z0-9·&]{2,15}{suffix})'
                matches = re.findall(pattern, line)
                found_companies.update(matches)

        # 模式2: 知名大公司（短名称直接匹配）
        big_companies = [
            '腾讯', '阿里', '阿里巴巴', '百度', '字节跳动', '字节', '美团',
            '京东', '华为', '小米', '比亚迪', '大疆', '网易', '滴滴', '快手',
            '拼多多', '蚂蚁集团', '蚂蚁金服', '微软', '谷歌', '苹果', '亚马逊',
            'Meta', '特斯拉', 'OpenAI', 'DeepSeek',
        ]
        for company in big_companies:
            if company in line:
                found_companies.add(company)

    return list(found_companies)
