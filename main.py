# coding=utf-8

import gitlab
import pandas as pd

gl = gitlab.Gitlab('https://gitlab.xxx.com', private_token='xxx', timeout=50, api_version='4')

start_time = '2022-02-19T00:00:00Z'
end_time = '2022-03-20T23:59:00Z'


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
    csv("./gitlab.csv")
