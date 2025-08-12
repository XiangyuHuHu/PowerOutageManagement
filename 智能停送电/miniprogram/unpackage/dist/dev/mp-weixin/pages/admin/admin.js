"use strict";
const common_vendor = require("../../common/vendor.js");
const _sfc_main = {
  data() {
    return {
      userInfo: {}
    };
  },
  onLoad() {
    this.checkLogin();
    this.getUserInfo();
  },
  methods: {
    checkLogin() {
      const user = common_vendor.index.getStorageSync("user");
      if (!user) {
        common_vendor.index.reLaunch({ url: "/pages/login/login" });
      }
    },
    getUserInfo() {
      const user = common_vendor.index.getStorageSync("user");
      if (user) {
        this.userInfo = user;
      }
    },
    goToApproval() {
      common_vendor.index.showLoading({ title: "加载中..." });
      common_vendor.index.navigateTo({
        url: "/pages/approval/approval",
        timeout: 5e3,
        success: () => {
          common_vendor.index.hideLoading();
        },
        fail: (err) => {
          common_vendor.index.hideLoading();
          common_vendor.index.__f__("error", "at pages/admin/admin.vue:123", "跳转到审批页面失败:", err);
          common_vendor.index.showToast({
            title: "页面跳转失败",
            icon: "none"
          });
        }
      });
    },
    goToStats() {
      common_vendor.index.showLoading({ title: "加载中..." });
      common_vendor.index.navigateTo({
        url: "/pages/stats/stats",
        timeout: 5e3,
        success: () => {
          common_vendor.index.hideLoading();
        },
        fail: (err) => {
          common_vendor.index.hideLoading();
          common_vendor.index.__f__("error", "at pages/admin/admin.vue:142", "跳转到统计页面失败:", err);
          common_vendor.index.showToast({
            title: "页面跳转失败",
            icon: "none"
          });
        }
      });
    },
    goToUserManagement() {
      common_vendor.index.showLoading({ title: "加载中..." });
      setTimeout(() => {
        common_vendor.index.navigateTo({
          url: "/pages/user_management/user_management",
          timeout: 1e4,
          // 增加到10秒
          success: () => {
            common_vendor.index.hideLoading();
            common_vendor.index.__f__("log", "at pages/admin/admin.vue:161", "用户管理页面跳转成功");
          },
          fail: (err) => {
            common_vendor.index.hideLoading();
            common_vendor.index.__f__("error", "at pages/admin/admin.vue:165", "跳转到用户管理页面失败:", err);
            if (err.errMsg && err.errMsg.includes("timeout")) {
              common_vendor.index.showModal({
                title: "页面跳转超时",
                content: "是否尝试重新跳转？",
                success: (res) => {
                  if (res.confirm) {
                    common_vendor.index.reLaunch({
                      url: "/pages/user_management/user_management",
                      fail: (reLaunchErr) => {
                        common_vendor.index.__f__("error", "at pages/admin/admin.vue:178", "reLaunch也失败了:", reLaunchErr);
                        common_vendor.index.showToast({
                          title: "页面跳转失败，请检查网络",
                          icon: "none",
                          duration: 3e3
                        });
                      }
                    });
                  }
                }
              });
            } else {
              common_vendor.index.showToast({
                title: "页面跳转失败",
                icon: "none",
                duration: 3e3
              });
            }
          }
        });
      }, 100);
    },
    goToRepair() {
      common_vendor.index.showLoading({ title: "加载中..." });
      common_vendor.index.navigateTo({
        url: "/pages/repair/repair",
        timeout: 5e3,
        success: () => {
          common_vendor.index.hideLoading();
        },
        fail: (err) => {
          common_vendor.index.hideLoading();
          common_vendor.index.__f__("error", "at pages/admin/admin.vue:211", "跳转到检修页面失败:", err);
          common_vendor.index.showToast({
            title: "页面跳转失败",
            icon: "none"
          });
        }
      });
    },
    logout() {
      common_vendor.index.showModal({
        title: "确认退出",
        content: "确定要退出登录吗？",
        success: (res) => {
          if (res.confirm) {
            common_vendor.index.clearStorageSync();
            common_vendor.index.reLaunch({
              url: "/pages/login/login"
            });
          }
        }
      });
    },
    goToSimpleUserManagement() {
      common_vendor.index.__f__("log", "at pages/admin/admin.vue:236", "跳转到简化版用户管理页面");
      common_vendor.index.showLoading({ title: "加载中..." });
      common_vendor.index.navigateTo({
        url: "/pages/user_management_simple/user_management_simple",
        timeout: 1e4,
        success: () => {
          common_vendor.index.hideLoading();
          common_vendor.index.__f__("log", "at pages/admin/admin.vue:243", "简化版用户管理页面跳转成功");
        },
        fail: (err) => {
          common_vendor.index.hideLoading();
          common_vendor.index.__f__("error", "at pages/admin/admin.vue:247", "简化版用户管理页面跳转失败:", err);
          common_vendor.index.showToast({
            title: "页面跳转失败",
            icon: "none"
          });
        }
      });
    },
    goToLightUserManagement() {
      common_vendor.index.__f__("log", "at pages/admin/admin.vue:257", "跳转到轻量版用户管理页面");
      common_vendor.index.showLoading({ title: "加载中..." });
      common_vendor.index.navigateTo({
        url: "/pages/user_management_light/user_management_light",
        timeout: 1e4,
        success: () => {
          common_vendor.index.hideLoading();
          common_vendor.index.__f__("log", "at pages/admin/admin.vue:264", "轻量版用户管理页面跳转成功");
        },
        fail: (err) => {
          common_vendor.index.hideLoading();
          common_vendor.index.__f__("error", "at pages/admin/admin.vue:268", "轻量版用户管理页面跳转失败:", err);
          common_vendor.index.showToast({
            title: "页面跳转失败",
            icon: "none"
          });
        }
      });
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return {
    a: common_vendor.t($data.userInfo.username || "管理员"),
    b: common_vendor.t($data.userInfo.role || "管理员"),
    c: common_vendor.o((...args) => $options.goToApproval && $options.goToApproval(...args)),
    d: common_vendor.o((...args) => $options.goToStats && $options.goToStats(...args)),
    e: common_vendor.o((...args) => $options.goToUserManagement && $options.goToUserManagement(...args)),
    f: common_vendor.o((...args) => $options.goToRepair && $options.goToRepair(...args)),
    g: common_vendor.o((...args) => $options.logout && $options.logout(...args)),
    h: common_vendor.o((...args) => $options.goToSimpleUserManagement && $options.goToSimpleUserManagement(...args)),
    i: common_vendor.o((...args) => $options.goToLightUserManagement && $options.goToLightUserManagement(...args))
  };
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/admin/admin.js.map
