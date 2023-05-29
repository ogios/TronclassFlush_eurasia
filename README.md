# TronclassFlush
刷欧亚畅课课程访问量的小程序

## 基础登录方法
登录在2-25号已经解决了， 很小的组件  
传送门: [TronclassLogin_eurasia](https://github.com/ogios/TronclassLogin_eurasia)

## 食用指北

> conf.ini不存在会自行创建

使用flush.py文件, 需要安装的第三方库:
```bat
pip install alive_progress, requests, click
```


```bat
python .\flush.py -u "<username>" -p "<password>" -url "<course_url>" -count <count>
```
~~使用flush.exe文件:~~ 取消了，可以自行下下来打包


### session与课程获取
之前是需要需要手动去浏览器里登录然后提取，也没有使用自动化解决，不想程序太臃肿

现在是通过写好的登录类 `Login` 去登录然后返回 `SSO` 对象进行请求，具体可以去看上面的传送门

课程就是直接进入需要刷的课程的页面，复制网页链接传入 `-url ` 后面即可。**注意: 是需要进入课程页面**

## 测试页面
~~本人用flask暂时做了一个测试交互页面，并非永久开启，随时可能关闭：~~  

~~可能存在无效的刷新，不稳定~~

已经关闭了，有莫名其妙的访问ip，有点怪


