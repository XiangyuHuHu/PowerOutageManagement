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
    common_vendor.index.__f__("log", "at pages/user_management_simple/user_management_simple.vue:35", "简化版用户管理页面加载");
    this.fetchUsers();
  },
  methods: {
    goBack() {
      common_vendor.index.navigateBack();
    },
    async fetchUsers() {
      common_vendor.index.__f__("log", "at pages/user_management_simple/user_management_simple.vue:45", "开始获取用户列表");
      this.loading = true;
      try {
        const response = await common_vendor.index.request({
          url: "http://localhost:5050/api/mp/users",
          method: "GET",
          timeout: 1e4
        });
        common_vendor.index.__f__("log", "at pages/user_management_simple/user_management_simple.vue:55", "响应:", response);
        if (response.statusCode === 200) {
          this.users = response.data;
          common_vendor.index.__f__("log", "at pages/user_management_simple/user_management_simple.vue:59", "获取到", this.users.length, "个用户");
        } else {
          common_vendor.index.__f__("error", "at pages/user_management_simple/user_management_simple.vue:61", "请求失败:", response.statusCode);
        }
      } catch (err) {
        common_vendor.index.__f__("error", "at pages/user_management_simple/user_management_simple.vue:64", "网络错误:", err);
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
        b: common_vendor.t(user.role),
        c: user.id
      };
    })
  }, {
    d: common_vendor.o((...args) => $options.fetchUsers && $options.fetchUsers(...args))
  });
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/user_management_simple/user_management_simple.js.map
