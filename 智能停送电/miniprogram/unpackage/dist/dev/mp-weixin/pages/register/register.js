"use strict";
const common_vendor = require("../../common/vendor.js");
const _sfc_main = {
  data() {
    return {
      form: {
        username: "",
        password: "",
        confirmPassword: "",
        realname: "",
        role: "electrician"
      },
      roleOptions: ["电工", "调度员"],
      roleIndex: 0,
      loading: false,
      error: ""
    };
  },
  methods: {
    onRoleChange(e) {
      this.roleIndex = e.detail.value;
      this.form.role = this.roleIndex === 0 ? "electrician" : "dispatcher";
    },
    validateForm() {
      if (!this.form.username.trim()) {
        this.error = "请输入用户名";
        return false;
      }
      if (this.form.username.length < 3) {
        this.error = "用户名至少需要3个字符";
        return false;
      }
      if (!this.form.password.trim()) {
        this.error = "请输入密码";
        return false;
      }
      if (this.form.password.length < 6) {
        this.error = "密码至少需要6个字符";
        return false;
      }
      if (this.form.password !== this.form.confirmPassword) {
        this.error = "两次输入的密码不一致";
        return false;
      }
      if (!this.form.realname.trim()) {
        this.error = "请输入真实姓名";
        return false;
      }
      this.error = "";
      return true;
    },
    async register() {
      if (!this.validateForm()) {
        return;
      }
      this.loading = true;
      this.error = "";
      try {
        const response = await common_vendor.index.request({
          url: "http://localhost:5050/api/register",
          method: "POST",
          data: {
            username: this.form.username,
            password: this.form.password,
            realname: this.form.realname,
            role: this.form.role
          },
          header: {
            "Content-Type": "application/json"
          }
        });
        if (response.statusCode === 200) {
          common_vendor.index.showToast({
            title: "注册成功",
            icon: "success"
          });
          setTimeout(() => {
            common_vendor.index.navigateTo({
              url: "/pages/login/login"
            });
          }, 1500);
        } else {
          this.error = response.data.msg || "注册失败";
        }
      } catch (err) {
        common_vendor.index.__f__("error", "at pages/register/register.vue:181", "注册失败:", err);
        this.error = "网络错误，请稍后重试";
      } finally {
        this.loading = false;
      }
    },
    goToLogin() {
      common_vendor.index.navigateTo({
        url: "/pages/login/login"
      });
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return common_vendor.e({
    a: $data.form.username,
    b: common_vendor.o(($event) => $data.form.username = $event.detail.value),
    c: $data.form.password,
    d: common_vendor.o(($event) => $data.form.password = $event.detail.value),
    e: $data.form.confirmPassword,
    f: common_vendor.o(($event) => $data.form.confirmPassword = $event.detail.value),
    g: $data.form.realname,
    h: common_vendor.o(($event) => $data.form.realname = $event.detail.value),
    i: common_vendor.t($data.roleOptions[$data.roleIndex]),
    j: $data.roleIndex,
    k: $data.roleOptions,
    l: common_vendor.o((...args) => $options.onRoleChange && $options.onRoleChange(...args)),
    m: $data.loading
  }, $data.loading ? {} : {}, {
    n: common_vendor.o((...args) => $options.register && $options.register(...args)),
    o: $data.loading,
    p: common_vendor.o((...args) => $options.goToLogin && $options.goToLogin(...args)),
    q: $data.error
  }, $data.error ? {
    r: common_vendor.t($data.error)
  } : {});
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-bac4a35d"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/register/register.js.map
