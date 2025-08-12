# 智能停送电系统 - 小程序端

## 📁 目录结构

```
miniprogram/
├── pages/                    # 页面文件
│   ├── index/               # 首页
│   ├── login/               # 登录页
│   ├── apply/               # 申请页
│   ├── approval/            # 审批页
│   ├── repair/              # 检修页
│   └── ...
├── components/              # 组件
│   ├── page-head/          # 页面头部
│   ├── page-foot/          # 页面底部
│   └── ...
├── store/                   # 状态管理
│   ├── index.js            # Store入口
│   └── counter.js          # 计数器
├── static/                  # 静态资源
│   ├── icons/              # 图标
│   ├── image/              # 图片
│   └── font/               # 字体
├── uni_modules/            # uni-app模块
├── wxcomponents/           # 微信小程序组件
├── App.vue                 # 应用入口
├── main.js                 # 主入口
├── pages.json              # 页面配置
├── manifest.json           # 应用配置
└── uni.scss               # 全局样式
```

## 🚀 快速启动

### 开发环境
```bash
# 安装依赖
npm install

# HBuilderX打开项目
# 或使用命令行
uni build
```

### 发布部署
```bash
# 构建H5版本
uni build -p h5

# 构建微信小程序
uni build -p mp-weixin

# 构建APP版本
uni build -p app
```

## 📱 支持的平台

- ✅ 微信小程序
- ✅ H5网页版
- ✅ APP (Android/iOS)
- ✅ 支付宝小程序
- ✅ 百度小程序

## 🔧 功能特性

### 用户功能
- ✅ 用户登录/注册
- ✅ 角色权限管理
- ✅ 个人信息管理

### 申请功能
- ✅ 停电申请提交
- ✅ 送电申请提交
- ✅ 申请状态跟踪
- ✅ 申请历史查看

### 审批功能
- ✅ 申请审批处理
- ✅ 审批历史记录
- ✅ 审批状态更新

### 检修功能
- ✅ 检修任务管理
- ✅ 检修进度跟踪
- ✅ 检修报告提交

### 系统功能
- ✅ 消息通知
- ✅ 数据统计
- ✅ 系统设置

## 📋 页面说明

### 主要页面
- **首页**: 功能导航和快捷入口
- **登录页**: 用户身份验证
- **申请页**: 停电/送电申请提交
- **审批页**: 申请审批处理
- **检修页**: 检修任务管理
- **统计页**: 数据统计展示
- **设置页**: 系统配置管理

### 组件说明
- **page-head**: 统一的页面头部
- **page-foot**: 统一的页面底部
- **u-link**: 链接组件
- **u-charts**: 图表组件

## 🛠️ 开发指南

### 添加新页面
1. 在`pages/`中创建页面目录
2. 创建页面文件（.vue）
3. 在`pages.json`中配置路由
4. 添加页面权限控制

### 添加新组件
1. 在`components/`中创建组件
2. 在页面中引入使用
3. 添加组件文档

### 状态管理
1. 在`store/`中添加状态
2. 在页面中使用状态
3. 实现数据持久化

### API调用
1. 在`common/`中定义API
2. 在页面中调用API
3. 处理请求响应

## 📊 配置说明

### 环境配置
```javascript
// 开发环境
const DEV_API = 'http://localhost:5050'

// 生产环境
const PROD_API = 'https://your-domain.com'

// 测试环境
const TEST_API = 'https://test-domain.com'
```

### 权限配置
```javascript
// 角色权限
const ROLE_PERMISSIONS = {
  admin: ['all'],
  dispatcher: ['approval', 'history'],
  electrician: ['apply', 'repair'],
  user: ['apply', 'view']
}
```

## 🔍 调试工具

- **HBuilderX**: 官方IDE，支持真机调试
- **微信开发者工具**: 微信小程序调试
- **Chrome DevTools**: H5版本调试
- **uni-app调试器**: 跨平台调试

## 📝 发布流程

### 微信小程序
1. 在微信公众平台注册小程序
2. 配置服务器域名
3. 上传代码审核
4. 发布上线

### H5版本
1. 构建H5版本
2. 部署到Web服务器
3. 配置域名和SSL
4. 测试功能

### APP版本
1. 申请开发者账号
2. 配置证书和签名
3. 打包生成APK/IPA
4. 上传应用商店

## 🎨 设计规范

### 颜色规范
- 主色调: #409eff
- 成功色: #67c23a
- 警告色: #e6a23c
- 错误色: #f56c6c

### 字体规范
- 主标题: 20px
- 副标题: 16px
- 正文: 14px
- 说明文字: 12px

### 间距规范
- 页面边距: 20px
- 组件间距: 10px
- 文字行高: 1.5

