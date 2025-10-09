"use strict";
const common_vendor = require("../../common/vendor.js");
const _sfc_main = {
  data() {
    return {
      users: [],
      loading: false
    };
  },
  onLoad() {
    common_vendor.index.__f__("log", "at pages/user_management_light/user_management_light.vue:48", "轻量级用户管理页面加载");
    setTimeout(() => {
      this.fetchUsers();
    }, 500);
  },
  methods: {
    goBack() {
      common_vendor.index.navigateBack();
    },
    getRoleText(role) {
      const roleMap = {
        "admin": "管理员",
        "dispatcher": "调度员",
        "electrician": "电工",
        "user": "普通用户"
      };
      return roleMap[role] || role;
    },
    async fetchUsers() {
      common_vendor.index.__f__("log", "at pages/user_management_light/user_management_light.vue:71", "开始获取用户列表");
      this.loading = true;
      try {
        const response = await common_vendor.index.request({
          url: "http://localhost:5050/api/mp/users",
          method: "GET",
          timeout: 1e4
        });
        common_vendor.index.__f__("log", "at pages/user_management_light/user_management_light.vue:81", "用户列表响应:", response);
        if (response.statusCode === 200) {
          this.users = response.data;
          common_vendor.index.__f__("log", "at pages/user_management_light/user_management_light.vue:85", "用户列表获取成功，共", this.users.length, "个用户");
        } else {
          common_vendor.index.__f__("error", "at pages/user_management_light/user_management_light.vue:87", "获取用户列表失败，状态码:", response.statusCode);
          common_vendor.index.showToast({
            title: "获取用户列表失败",
            icon: "none"
          });
        }
      } catch (err) {
        common_vendor.index.__f__("error", "at pages/user_management_light/user_management_light.vue:94", "获取用户列表失败:", err);
        common_vendor.index.showToast({
          title: "网络错误",
          icon: "none"
        });
      } finally {
        this.loading = false;
      }
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return common_vendor.e({
    a: common_vendor.o((...args) => $options.goBack && $options.goBack(...args)),
    b: $data.loading
  }, $data.loading ? {} : {
    c: common_vendor.f($data.users, (user, k0, i0) => {
      return {
        a: common_vendor.t(user.realname),
        b: common_vendor.t(user.username),
        c: common_vendor.t($options.getRoleText(user.role)),
        d: user.id
      };
    })
  }, {
    d: !$data.loading && $data.users.length > 0
  }, !$data.loading && $data.users.length > 0 ? {
    e: common_vendor.t($data.users.length)
  } : {}, {
    f: common_vendor.t($data.loading ? "刷新中..." : "刷新"),
    g: common_vendor.o((...args) => $options.fetchUsers && $options.fetchUsers(...args)),
    h: $data.loading
  });
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/user_management_light/user_management_light.js.map
