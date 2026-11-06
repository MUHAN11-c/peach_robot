# 预处理与特征检测当前逻辑

2026-11-06 按 preprocessor.py、feature_extractor.py、config.py 及流水线门面核对。这里只解释深度带/几何基线；可替换的 rembg、MobileSAM、DINOv2 档见 [包 README](README.md)。当前包没有本文旧版所述的 C++ 实现。

## Preprocessor

入口 `preprocess(depth_image, color_image, binary_threshold_min, binary_threshold_max)` 返回连通域掩码列表和可选白底彩色图。处理顺序为：

1. `_threshold`：原始深度落在闭区间 lo..hi 且有效时置 255。uint16 排除 0/65535，float 排除 0/NaN；不做旧文档中的零值插值。
2. `_morph_clean`：椭圆核开运算去噪、闭运算填洞；核小于 3 时跳过，偶数核上调为奇数。
3. `_extract_components`：8 连通提取，仅按面积范围过滤并降序，component_max_count>0 时截断。不在此阶段做宽高或长宽比筛选。
4. 有彩色图和掩码时，`_extract_color` 只使用第一个（面积最大）掩码，可先膨胀，再抠到白底图；不是合并所有候选。

类内回退默认包括深度带 1818..2045、面积 0..100000、最多 3 个、开核 3/闭核 9/抠图膨胀核 5。实际节点/Web 会应用配置和调试值，不能把类内默认当作部署默认。

## FeatureExtractor

`extract_features` 先调用 filter_components，按非零面积、外接框最小宽高及 `min(w,h)/max(w,h)` 筛选，再按面积排序。随后顺序处理候选；当前没有线程池或 max_threads 控制。异常/无效候选会被跳过，输出索引不保证与原输入一一对应。

每个成功候选提取工件外接大圆、形态学腐蚀/最大连通域/膨胀得到的阀体小圆，并计算工件中心指向阀体中心的 atan2 角。ComponentFeature 保存圆心/半径/面积、弧度及度、掩码和可选彩色图引用。找不到有效圆时可返回无特征，不保证每个连通域都产出位姿。

后续由 PosePipeline 选择 matcher，PoseEstimator 根据匹配模板、目标中心深度与变换合成位姿；默认几何匹配和可选学习匹配是不同档案，不能只凭本阶段特征断言最终匹配方式。

## 参数来源

`config/pose_estimation.yaml` 是当前算法配置来源；ConfigReader 先解析源码配置，再找 ament share，最后才尝试旧 Web 路径。`web_ui/configs/default_config.yaml` 当前只是兼容占位。

Web 滑块通过 apply_debug_param 更新进程内配置，经 ParamsManager 写 debug_thresholds.json，再通知 ROS 的 update_params；不能把 JSON 描述成仅供 UI 回显。两阶段类的默认筛选范围不同，运行时应用哪些参数须看调用者，不保证所有阈值天然相同。

本轮只核对源码，未运行图像处理或复验历史精度。
