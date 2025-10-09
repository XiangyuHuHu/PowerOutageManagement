"use strict";
const common_vendor = require("../../common/vendor.js");
const _sfc_main = {
  data() {
    return {
      form: {
        username: "",
        password: ""
      }
    };
  },
  methods: {
    login() {
      const { username, password } = this.form;
      if (!username || !password) {
        common_vendor.index.showToast({ title: "请填写用户名和密码", icon: "none" });
        return;
      }
      common_vendor.index.request({
        url: "http://localhost:5050/api/login",
        method: "POST",
        header: { "Content-Type": "application/json" },
        data: this.form,
        success: (res) => {
          if (res.statusCode === 200) {
            common_vendor.index.setStorageSync("user", res.data);
            if (res.data && res.data.role) {
              common_vendor.index.setStorageSync("user_role", res.data.role);
              common_vendor.index.__f__("log", "at pages/login/login.vue:59", "保存用户角色:", res.data.role);
            }
            if (res.data && res.data.role) {
              const role = res.data.role;
              if (role === "electrician") {
                common_vendor.index.reLaunch({ url: "/pages/electrician_home/electrician_home" });
              } else if (role === "dispatcher") {
                common_vendor.index.reLaunch({ url: "/pages/dispatcher_home/dispatcher_home" });
              } else if (role === "admin") {
                common_vendor.index.reLaunch({ url: "/pages/admin/admin" });
              } else {
                common_vendor.index.reLaunch({ url: "/pages/index/index" });
              }
            }
          } else {
            common_vendor.index.showToast({ title: res.data.msg || "登录失败", icon: "error" });
          }
        },
        fail: () => {
          common_vendor.index.showToast({ title: "网络错误", icon: "error" });
        }
      });
    },
    goToRegister() {
      common_vendor.index.navigateTo({
        url: "/pages/register/register"
      });
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return {
    a: $data.form.username,
    b: common_vendor.o(($event) => $data.form.username = $event.detail.value),
    c: $data.form.password,
    d: common_vendor.o(($event) => $data.form.password = $event.detail.value),
    e: common_vendor.o((...args) => $options.login && $options.login(...args)),
    f: common_vendor.o((...args) => $options.goToRegister && $options.goToRegister(...args))
  };
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/login/login.js.map
