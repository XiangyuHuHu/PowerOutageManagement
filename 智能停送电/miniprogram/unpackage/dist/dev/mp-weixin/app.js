"use strict";
Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
const common_vendor = require("./common/vendor.js");
const store_index = require("./store/index.js");
if (!Math) {
  "./pages/login/login.js";
  "./pages/register/register.js";
  "./pages/electrician_home/electrician_home.js";
  "./pages/dispatcher_home/dispatcher_home.js";
  "./pages/power_on_apply/power_on_apply.js";
  "./pages/approval/approval.js";
  "./pages/approval/history.js";
  "./pages/approval/detail.js";
  "./pages/apply/apply.js";
  "./pages/poweroff/verify.js";
  "./pages/poweroff/repair.js";
  "./pages/poweroff/restore.js";
  "./pages/admin/admin.js";
  "./pages/user_management/user_management.js";
  "./pages/user_management_simple/user_management_simple.js";
  "./pages/user_management_light/user_management_light.js";
  "./pages/stats/stats.js";
  "./pages/repair/repair.js";
  "./pages/index/index.js";
}
const _sfc_main = {
  onLaunch: function() {
    common_vendor.index.__f__("log", "at App.vue:23", "App Launch");
  },
  onShow: function() {
    common_vendor.index.__f__("log", "at App.vue:48", "App Show");
  },
  onHide: function() {
    common_vendor.index.__f__("log", "at App.vue:51", "App Hide");
  },
  globalData: {
    test: ""
  },
  methods: {
    ...common_vendor.mapMutations(["setUniverifyErrorMsg", "setUniverifyLogin"])
  }
};
function createApp() {
  const app = common_vendor.createSSRApp(_sfc_main);
  app.use(store_index.store);
  app.use(common_vendor.createPinia());
  app.config.globalProperties.$adpid = "1111111111";
  app.config.globalProperties.$backgroundAudioData = {
    playing: false,
    playTime: 0,
    formatedPlayTime: "00:00:00"
  };
  return {
    app,
    Vuex: common_vendor.index$1,
    // 如果 nvue 使用 vuex 的各种map工具方法时，必须 return Vuex
    Pinia: common_vendor.Pinia
    // 此处必须将 Pinia 返回
  };
}
createApp().app.mount("#app");
exports.createApp = createApp;
//# sourceMappingURL=../.sourcemap/mp-weixin/app.js.map
