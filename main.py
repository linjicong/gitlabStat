# coding=utf-8

import gitlab
import pandas as pd
from collections import defaultdict
import os

url=os.getenv("url")
private_token=os.getenv("private_token")

gl = gitlab.Gitlab(url=url, private_token=private_token, timeout=50, api_version='4')

start_time = '2022-12-19T00:00:00Z'
end_time = '2023-01-20T23:59:00Z'


def getLines(c, exts):
    diffs = c.diff()
    sum = 0
    for diff in diffs:
        if (diff['old_path'].split(".")[-1].lower() in exts) or (diff['new_path'].split(".")[-1].lower() in exts):
            sum += len(diff['diff'].splitlines())
    return sum


def get_gitlab():
    """
    gitlab API
    """
    list2 = []
    projects = gl.projects.list( all=True)
    num = 0
    print("projects = ", projects)
    for project in projects:
        num += 1

        print(f"查看第{num:02d}个项目：{project.name}")
        for branch in project.branches.list():
            # print("branch = ", branch)
            commits = project.commits.list(all=True, query_parameters={'since': start_time, 'until': end_time,
                                                                       'ref_name': branch.name})

            for commit in commits:
                com = project.commits.get(commit.id)
                if com.message.startswith("Merge "):
                    # print('跳过merge产生的commit:{},{}'.format(com.short_id, com.message))
                    continue

                pro = {}
                try:
                    # if com.stats['additions'] > 2000:
                    #     print(f"{project.name}--> {branch.name} --> {com.id} ==> {com.stats['additions']}")
                    #     continue
                    # print(project.path_with_namespace,com.author_name,com.stats["total"])
                    pro["projectName"] = project.path_with_namespace
                    pro["authorName"] = com.author_name
                    pro["branch"] = branch.name
                    pro["additions"] = com.stats["additions"]
                    pro['lines'] = getLines(com,
                                            ['java', 'c', 'js', 'm', 'h', 'cpp', 'cc', 'html', 'css', 'scss', 'vue',
                                             'jsx', 'kt', 'yml', 'yaml', 'xml', 'gradle','ts','json'])
                    pro["deletions"] = com.stats["deletions"]
                    pro["commitNum"] = com.stats["total"]
                    list2.append(pro)
                except:
                    print("有错误, 请检查")

    return list2

def get_user():
    users = gl.users.list(all=True)
    result = []
    for user in users:
        u = {}
        u['id'] = user.id
        u['name'] = user.name
        result.append(u)
    return result

def get_projects():
    projects = gl.projects.list(all=True)
    result=[]
    for project in projects:
        pro = {}
        pro['id']=project.id
        pro['name']=project.name
        pro['description']=project.description
        result.append(pro)
    return result

"""
执行速度很慢
"""
def get_user_projects():
    users = gl.users.list(active=True, all=True)  # 拿到所有用户
    projects = gl.projects.list(all=True)  # 拿到所有项目
    groups = gl.groups.list(all=True)  # 拿到所有项目
    u = [user.name for user in users]  # 生成用户列表
    for i in u:  # 只包含除组以外个人加入的项目
        name_dict = defaultdict(list)
        for project in projects:
            # print(project.id, project.name)
            members = project.members.list()  # 项目下的成员列表，非继承，要继承父项目人员设置为project.members.list(all=True)
            a = [me.name for me in members]
            if i in tuple(a):
                name_dict[i].append(project.path_with_namespace)  # 生成以用户名为key，项目名为value列表的字典
        print(name_dict)

    for i in u:  # 只包含人所在的组
        name_dict = defaultdict(list)
        for group in groups:
            # print(project.id, project.name)
            members = group.members.list()
            a = [me.name for me in members]
            if i in tuple(a):
                name_dict[i].append(group.full_path)  # 拿到用户拥有的所有组
        print(name_dict)
def create_user():
    data={
        "username":"chenxueying2",
        "name":"chenxueying2",
        "email":"chenxueying2@zy.com",
        "provider":"ldapmain",
        "extern_uid":"cn=chenxueying2,ou=persons,dc=pub,dc=org",
        "reset_password":"true",
        "skip_confirmation":"true"
    }
    create = gl.users.create(data)
    print(create)


def data():
    """
    数据去重
    key split
    """

    ret = {}

    for ele in get_gitlab():
        key = ele["projectName"] + ele["authorName"] + ele["branch"]
        if key not in ret:
            ret[key] = ele
            ret[key]["commitTotal"] = 1
        else:
            ret[key]["additions"] += ele["additions"]
            ret[key]["deletions"] += ele["deletions"]
            ret[key]["commitNum"] += ele["commitNum"]
            ret[key]["commitTotal"] += 1

    list1 = []
    for key, v in ret.items():
        v["项目名"] = v.pop("projectName")
        v["开发者"] = v.pop("authorName")
        v["分支"] = v.pop("branch")
        v['代码量'] = v.pop("lines")
        v["添加代码行数"] = v.pop("additions")
        v["删除代码行数"] = v.pop("deletions")
        v["提交总行数"] = v.pop("commitNum")
        v["提交次数"] = v["commitTotal"]
        list1.append(v)
    print(list1)
    return list1


def csv(csvName):
    """
    csv
    """

    df = pd.DataFrame(data(), columns=["项目名", "开发者", "分支", "添加代码行数", "删除代码行数", "提交总行数", "提交次数"])
    df.to_csv(csvName, index=False, encoding="utf_8_sig")


if __name__ == "__main__":
    # csv("./gitlab.csv")
    # create_user()
    # get_user()
    # get_projects()
    df = pd.DataFrame(get_user())
    df.to_csv("users.csv", index=False, encoding="utf_8_sig")