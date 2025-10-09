"use strict";
const common_vendor = require("../../common/vendor.js");
const _sfc_main = {
  data() {
    return {
      form: {
        applicant: "",
        date: "",
        deviceId: "",
        reason: ""
      },
      deviceOptions: ["配电柜A1", "配电柜A2", "配电柜B1"],
      reasonOptions: ["线路检修", "设备维护", "其他"]
    };
  },
  onLoad() {
    const user = common_vendor.index.getStorageSync("user");
    if (user && user.realname) {
      this.form.applicant = user.realname;
    } else if (user && user.username) {
      this.form.applicant = user.username;
    }
  },
  methods: {
    onDeviceChange(e) {
      this.form.deviceId = this.deviceOptions[e.detail.value];
    },
    onReasonChange(e) {
      this.form.reason = this.reasonOptions[e.detail.value];
    },
    submitForm() {
      const { applicant, date, deviceId, reason } = this.form;
      if (!applicant || !date || !deviceId || !reason) {
        common_vendor.index.showToast({ title: "请填写完整", icon: "none" });
        return;
      }
      common_vendor.index.request({
        url: "http://localhost:5050/api/mp/power-apply",
        method: "POST",
        header: { "Content-Type": "application/json" },
        data: this.form,
        timeout: 1e4,
        success: (res) => {
          if (res.statusCode === 200) {
            common_vendor.index.showToast({ title: "提交成功", icon: "success" });
            setTimeout(() => common_vendor.index.navigateBack(), 1500);
          } else {
            common_vendor.index.showToast({ title: res.data.msg || "提交失败", icon: "error" });
          }
        },
        fail: () => {
          common_vendor.index.showToast({ title: "网络错误", icon: "error" });
        }
      });
    }
  }
};
if (!Array) {
  const _easycom_uni_datetime_picker2 = common_vendor.resolveComponent("uni-datetime-picker");
  _easycom_uni_datetime_picker2();
}
const _easycom_uni_datetime_picker = () => "../../uni_modules/uni-datetime-picker/components/uni-datetime-picker/uni-datetime-picker.js";
if (!Math) {
  _easycom_uni_datetime_picker();
}
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return {
    a: $data.form.applicant,
    b: common_vendor.o(($event) => $data.form.applicant = $event.detail.value),
    c: common_vendor.o(($event) => $data.form.date = $event),
    d: common_vendor.p({
      type: "datetime",
      modelValue: $data.form.date
    }),
    e: common_vendor.t($data.form.deviceId || "请选择设备编号"),
    f: $data.deviceOptions,
    g: common_vendor.o((...args) => $options.onDeviceChange && $options.onDeviceChange(...args)),
    h: common_vendor.t($data.form.reason || "请选择停电原因"),
    i: $data.reasonOptions,
    j: common_vendor.o((...args) => $options.onReasonChange && $options.onReasonChange(...args)),
    k: common_vendor.o((...args) => $options.submitForm && $options.submitForm(...args))
  };
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/apply/apply.js.map
