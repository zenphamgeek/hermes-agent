# BỘ TỪ ĐIỂN MANIM MASTER (MANIM DICTIONARY & REGISTRY)

> **Single Source of Truth** cho toàn bộ 100+ phân cảnh hoạt họa Manim trong hệ thống ZenPham.
> Thống kê phân loại theo tính chất **Động (Animation)** vs **Tĩnh (Static Frame)**, liên kết kịch bản phân cảnh và **căn cứ khoa học / tiên đề toán học**.

---

## 1. Thống Kê Tổng Quan (Registry Overview)

- **Tổng số Scene đã xây dựng**: `100` phân cảnh
- **Hoạt họa động (`DYNAMIC_ANIMATION`)**: `99` scenes
- **Khung hình tĩnh (`STATIC_FRAME`)**: `1` scenes
- **Phân bổ theo Chuyên ngành**:
  - 🧠 **Trí Tuệ Nhân Tạo & Deep Learning (AI_ML)**: `56` scenes
  - 💻 **Khoa Học Máy Tính & Giải Thuật (CS_ALGO)**: `15` scenes
  - 📐 **Toán Học & Đại Số Tuyến Tính (PURE_MATH)**: `27` scenes
  - ⚡ **Vật Lý & Dao Động Cơ Học (PHYSICS)**: `1` scenes
  - 🧪 **Hóa Học & Phân Tử (CHEMISTRY)**: `1` scenes

---

## 2. Bảng Tra Cứu Nhanh 100+ Scenes (Quick Index)

| ID Scene | Tên Lớp (Class) | Ngành | Tính Chất | Lệnh Play | Căn Cứ Khoa Học Cốt Lõi | File Nguồn |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| `EP01_CoinPhysicsScene` | [`CoinPhysicsScene`](#ep01-coinphysicsscene) | 🧠 AI | 🎬 Động | `6` | Định lý Bayes & Phân phối Xác suất Tiền nghiệ... | `manim_tap_01_probability.py` |
| `EP01_BayesianUpdateScene` | [`BayesianUpdateScene`](#ep01-bayesianupdatescene) | 🧠 AI | 🎬 Động | `6` | Định lý Bayes & Phân phối Xác suất Tiền nghiệ... | `manim_tap_01_probability.py` |
| `EP01_AITokenProbabilityScene` | [`AITokenProbabilityScene`](#ep01-aitokenprobabilityscene) | 🧠 AI | 🎬 Động | `6` | Định lý Bayes & Phân phối Xác suất Tiền nghiệ... | `manim_tap_01_probability.py` |
| `EP02_LossLandscape3DScene` | [`LossLandscape3DScene`](#ep02-losslandscape3dscene) | 🧠 AI | 🎬 Động | `3` | Giải thuật Hạ Gradient Đa Chiều & Bề Mặt Hàm ... | `manim_tap_02_gradient_descent.py` |
| `EP02_GradientVectorFieldScene` | [`GradientVectorFieldScene`](#ep02-gradientvectorfieldscene) | 🧠 AI | 🎬 Động | `7` | Giải thuật Hạ Gradient Đa Chiều & Bề Mặt Hàm ... | `manim_tap_02_gradient_descent.py` |
| `EP02_LearningRateDilemmaScene` | [`LearningRateDilemmaScene`](#ep02-learningratedilemmascene) | 🧠 AI | 🎬 Động | `11` | Giải thuật Hạ Gradient Đa Chiều & Bề Mặt Hàm ... | `manim_tap_02_gradient_descent.py` |
| `EP02_OptimizerShowdownScene` | [`OptimizerShowdownScene`](#ep02-optimizershowdownscene) | 🧠 AI | 🎬 Động | `5` | Giải thuật Hạ Gradient Đa Chiều & Bề Mặt Hàm ... | `manim_tap_02_gradient_descent.py` |
| `EP02_BackpropComputationalGraphScene` | [`BackpropComputationalGraphScene`](#ep02-backpropcomputationalgraphscene) | 🧠 AI | 🎬 Động | `9` | Giải thuật Hạ Gradient Đa Chiều & Bề Mặt Hàm ... | `manim_tap_02_gradient_descent.py` |
| `EP03_VectorEmbeddingSpaceScene` | [`VectorEmbeddingSpaceScene`](#ep03-vectorembeddingspacescene) | 🧠 AI | 🎬 Động | `4` | Không Gian Nhúng Vector & Phép Đo Khoảng Cách... | `manim_tap_03_vector_embeddings.py` |
| `EP03_VectorArithmeticScene` | [`VectorArithmeticScene`](#ep03-vectorarithmeticscene) | 🧠 AI | 🎬 Động | `5` | Không Gian Nhúng Vector & Phép Đo Khoảng Cách... | `manim_tap_03_vector_embeddings.py` |
| `EP03_CosineSimilarityScene` | [`CosineSimilarityScene`](#ep03-cosinesimilarityscene) | 🧠 AI | 🎬 Động | `3` | Không Gian Nhúng Vector & Phép Đo Khoảng Cách... | `manim_tap_03_vector_embeddings.py` |
| `EP03_MatrixTransformationScene` | [`MatrixTransformationScene`](#ep03-matrixtransformationscene) | 🧠 AI | 🎬 Động | `2` | Không Gian Nhúng Vector & Phép Đo Khoảng Cách... | `manim_tap_03_vector_embeddings.py` |
| `EP03_AttentionProjectionScene` | [`AttentionProjectionScene`](#ep03-attentionprojectionscene) | 🧠 AI | 🎬 Động | `3` | Không Gian Nhúng Vector & Phép Đo Khoảng Cách... | `manim_tap_03_vector_embeddings.py` |
| `EP03_OneHotVsEmbeddingScene` | [`OneHotVsEmbeddingScene`](#ep03-onehotvsembeddingscene) | 🧠 AI | 🎬 Động | `2` | Không Gian Nhúng Vector & Phép Đo Khoảng Cách... | `manim_tap_03_vector_embeddings_v2.py` |
| `EP03_VectorArithmeticKingQueen` | [`VectorArithmeticKingQueen`](#ep03-vectorarithmetickingqueen) | 🧠 AI | 🎬 Động | `9` | Không Gian Nhúng Vector & Phép Đo Khoảng Cách... | `manim_tap_03_vector_embeddings_v2.py` |
| `EP03_CosineSimilarityResonance` | [`CosineSimilarityResonance`](#ep03-cosinesimilarityresonance) | 🧠 AI | 🎬 Động | `7` | Không Gian Nhúng Vector & Phép Đo Khoảng Cách... | `manim_tap_03_vector_embeddings_v2.py` |
| `EP04_SimpsonScatterRegressionScene` | [`SimpsonScatterRegressionScene`](#ep04-simpsonscatterregressionscene) | 📐 Math | 🎬 Động | `5` | Nghịch Lý Simpson & Hiện Tượng Đảo Chiều Thốn... | `manim_tap_04_simpson_paradox.py` |
| `EP04_ConfoundingVariable3DScene` | [`ConfoundingVariable3DScene`](#ep04-confoundingvariable3dscene) | 📐 Math | 🎬 Động | `2` | Nghịch Lý Simpson & Hiện Tượng Đảo Chiều Thốn... | `manim_tap_04_simpson_paradox.py` |
| `EP05_PRNGCycleModuloScene` | [`PRNGCycleModuloScene`](#ep05-prngcyclemoduloscene) | 💻 CS | 🎬 Động | `6` | Hàm Sinh Số Giả Ngẫu Nhiên PRNG & Entropy Mật... | `manim_tap_05_prng_entropy.py` |
| `EP05_TemperatureSamplingScene` | [`TemperatureSamplingScene`](#ep05-temperaturesamplingscene) | 💻 CS | 🎬 Động | `6` | Hàm Sinh Số Giả Ngẫu Nhiên PRNG & Entropy Mật... | `manim_tap_05_prng_entropy.py` |
| `EP05_PRNGCycleShortScene` | [`PRNGCycleShortScene`](#ep05-prngcycleshortscene) | 💻 CS | 🎬 Động | `6` | Hàm Sinh Số Giả Ngẫu Nhiên PRNG & Entropy Mật... | `manim_tap_05_prng_entropy.py` |
| `EP06_GaltonBoardScene` | [`GaltonBoardScene`](#ep06-galtonboardscene) | 📐 Math | 🎬 Động | `7` | Định Lý Giới Hạn Trung Tâm CLT & Phân Phối Ch... | `manim_tap_06_clt_gaussian.py` |
| `EP06_CLTConvergenceScene` | [`CLTConvergenceScene`](#ep06-cltconvergencescene) | 📐 Math | 🎬 Động | `5` | Định Lý Giới Hạn Trung Tâm CLT & Phân Phối Ch... | `manim_tap_06_clt_gaussian.py` |
| `EP06_GaussianWeightInitScene` | [`GaussianWeightInitScene`](#ep06-gaussianweightinitscene) | 📐 Math | 🎬 Động | `4` | Định Lý Giới Hạn Trung Tâm CLT & Phân Phối Ch... | `manim_tap_06_clt_gaussian.py` |
| `EP06_DiffusionNoiseDenoiseScene` | [`DiffusionNoiseDenoiseScene`](#ep06-diffusionnoisedenoisescene) | 📐 Math | 🎬 Động | `5` | Định Lý Giới Hạn Trung Tâm CLT & Phân Phối Ch... | `manim_tap_06_clt_gaussian.py` |
| `EP07_MSEParabolaScene` | [`MSEParabolaScene`](#ep07-mseparabolascene) | 🧠 AI | 🎬 Động | `4` | Hàm Mất Mát Cross-Entropy & Maximum Likelihoo... | `manim_tap_07_loss_function.py` |
| `EP07_CrossEntropyLogCurveScene` | [`CrossEntropyLogCurveScene`](#ep07-crossentropylogcurvescene) | 🧠 AI | 🎬 Động | `4` | Hàm Mất Mát Cross-Entropy & Maximum Likelihoo... | `manim_tap_07_loss_function.py` |
| `EP07_LossGradientVectorFlowScene` | [`LossGradientVectorFlowScene`](#ep07-lossgradientvectorflowscene) | 🧠 AI | 🎬 Động | `3` | Hàm Mất Mát Cross-Entropy & Maximum Likelihoo... | `manim_tap_07_loss_function.py` |
| `EP07_LossConvergenceValleyScene` | [`LossConvergenceValleyScene`](#ep07-lossconvergencevalleyscene) | 🧠 AI | 🎬 Động | `4` | Hàm Mất Mát Cross-Entropy & Maximum Likelihoo... | `manim_tap_07_loss_function.py` |
| `EP08_ChainRuleGraphScene` | [`ChainRuleGraphScene`](#ep08-chainrulegraphscene) | 🧠 AI | 🎬 Động | `6` | Thuật Toán Lan Truyền Ngược Backpropagation &... | `manim_tap_08_backpropagation.py` |
| `EP08_BackpropMultiLayerFlowScene` | [`BackpropMultiLayerFlowScene`](#ep08-backpropmultilayerflowscene) | 🧠 AI | 🎬 Động | `9` | Thuật Toán Lan Truyền Ngược Backpropagation &... | `manim_tap_08_backpropagation.py` |
| `EP08_VanishingExplodingGradientScene` | [`VanishingExplodingGradientScene`](#ep08-vanishingexplodinggradientscene) | 🧠 AI | 🎬 Động | `4` | Thuật Toán Lan Truyền Ngược Backpropagation &... | `manim_tap_08_backpropagation.py` |
| `EP08_AutogradComputationalGraphScene` | [`AutogradComputationalGraphScene`](#ep08-autogradcomputationalgraphscene) | 🧠 AI | 🎬 Động | `5` | Thuật Toán Lan Truyền Ngược Backpropagation &... | `manim_tap_08_backpropagation.py` |
| `EP09_OverfittingCurveClashScene` | [`OverfittingCurveClashScene`](#ep09-overfittingcurveclashscene) | 🧠 AI | 🎬 Động | `5` | Hiện Tượng Quá Khớp Overfitting & Đánh Đổi Độ... | `manim_tap_09_overfitting.py` |
| `EP09_L2RegularizationConstraintScene` | [`L2RegularizationConstraintScene`](#ep09-l2regularizationconstraintscene) | 🧠 AI | 🎬 Động | `6` | Hiện Tượng Quá Khớp Overfitting & Đánh Đổi Độ... | `manim_tap_09_overfitting.py` |
| `EP09_L1RegularizationDiamondScene` | [`L1RegularizationDiamondScene`](#ep09-l1regularizationdiamondscene) | 🧠 AI | 🎬 Động | `5` | Hiện Tượng Quá Khớp Overfitting & Đánh Đổi Độ... | `manim_tap_09_overfitting.py` |
| `EP09_DropoutNetworkSparsityScene` | [`DropoutNetworkSparsityScene`](#ep09-dropoutnetworksparsityscene) | 🧠 AI | 🎬 Động | `6` | Hiện Tượng Quá Khớp Overfitting & Đánh Đổi Độ... | `manim_tap_09_overfitting.py` |
| `EP10_CovarianceMatrixEllipseScene` | [`CovarianceMatrixEllipseScene`](#ep10-covariancematrixellipsescene) | 📐 Math | 🎬 Động | `4` | Phân Tích Thành Phần Chính PCA & Ma Trận Hiệp... | `manim_tap_10_pca_covariance.py` |
| `EP10_EigenvectorMaxVarianceScene` | [`EigenvectorMaxVarianceScene`](#ep10-eigenvectormaxvariancescene) | 📐 Math | 🎬 Động | `5` | Phân Tích Thành Phần Chính PCA & Ma Trận Hiệp... | `manim_tap_10_pca_covariance.py` |
| `EP10_PCAOrthogonalProjectionScene` | [`PCAOrthogonalProjectionScene`](#ep10-pcaorthogonalprojectionscene) | 📐 Math | 🎬 Động | `6` | Phân Tích Thành Phần Chính PCA & Ma Trận Hiệp... | `manim_tap_10_pca_covariance.py` |
| `EP10_LatentSpaceCompressionScene` | [`LatentSpaceCompressionScene`](#ep10-latentspacecompressionscene) | 📐 Math | 🎬 Động | `5` | Phân Tích Thành Phần Chính PCA & Ma Trận Hiệp... | `manim_tap_10_pca_covariance.py` |
| `EP11_QKVProjectionScene` | [`QKVProjectionScene`](#ep11-qkvprojectionscene) | 🧠 AI | 🎬 Động | `4` | Cơ Chế Scaled Dot-Product Attention (Query, K... | `manim_tap_11_attention_qkv.py` |
| `EP11_AttentionHeatmapClashScene` | [`AttentionHeatmapClashScene`](#ep11-attentionheatmapclashscene) | 🧠 AI | 🎬 Động | `4` | Cơ Chế Scaled Dot-Product Attention (Query, K... | `manim_tap_11_attention_qkv.py` |
| `EP11_WeightedValueSumScene` | [`WeightedValueSumScene`](#ep11-weightedvaluesumscene) | 🧠 AI | 🎬 Động | `4` | Cơ Chế Scaled Dot-Product Attention (Query, K... | `manim_tap_11_attention_qkv.py` |
| `EP11_MultiHeadAttentionPrismScene` | [`MultiHeadAttentionPrismScene`](#ep11-multiheadattentionprismscene) | 🧠 AI | 🎬 Động | `5` | Cơ Chế Scaled Dot-Product Attention (Query, K... | `manim_tap_11_attention_qkv.py` |
| `EP12_PositionalEncodingWaveScene` | [`PositionalEncodingWaveScene`](#ep12-positionalencodingwavescene) | 🧠 AI | 🎬 Động | `5` | Kiến Trúc Transformer Toàn Phần: Multi-Head A... | `manim_tap_12_transformer_architecture.py` |
| `EP12_TransformerBlockResidualScene` | [`TransformerBlockResidualScene`](#ep12-transformerblockresidualscene) | 🧠 AI | 🎬 Động | `7` | Kiến Trúc Transformer Toàn Phần: Multi-Head A... | `manim_tap_12_transformer_architecture.py` |
| `EP12_FeedForwardMemoryScene` | [`FeedForwardMemoryScene`](#ep12-feedforwardmemoryscene) | 🧠 AI | 🎬 Động | `5` | Kiến Trúc Transformer Toàn Phần: Multi-Head A... | `manim_tap_12_transformer_architecture.py` |
| `EP12_ScalingLawEmergenceScene` | [`ScalingLawEmergenceScene`](#ep12-scalinglawemergencescene) | 🧠 AI | 🎬 Động | `5` | Kiến Trúc Transformer Toàn Phần: Multi-Head A... | `manim_tap_12_transformer_architecture.py` |
| `EP13_ShannonEntropyCurveScene` | [`ShannonEntropyCurveScene`](#ep13-shannonentropycurvescene) | 💻 CS | 🎬 Động | `5` | Thuyết Thông Tin & Entropy Shannon (Claude Sh... | `manim_tap_13_entropy_shannon.py` |
| `EP13_CrossEntropyLossScene` | [`CrossEntropyLossScene`](#ep13-crossentropylossscene) | 💻 CS | 🎬 Động | `4` | Thuyết Thông Tin & Entropy Shannon (Claude Sh... | `manim_tap_13_entropy_shannon.py` |
| `EP13_KLDivergenceScene` | [`KLDivergenceScene`](#ep13-kldivergencescene) | 💻 CS | 🎬 Động | `4` | Thuyết Thông Tin & Entropy Shannon (Claude Sh... | `manim_tap_13_entropy_shannon.py` |
| `EP13_PerplexityBranchingScene` | [`PerplexityBranchingScene`](#ep13-perplexitybranchingscene) | 💻 CS | 🎬 Động | `6` | Thuyết Thông Tin & Entropy Shannon (Claude Sh... | `manim_tap_13_entropy_shannon.py` |
| `EP14_SoftmaxVectorTransformScene` | [`SoftmaxVectorTransformScene`](#ep14-softmaxvectortransformscene) | 🧠 AI | 🎬 Động | `6` | Hàm Softmax Nhiệt Độ (Temperature Scaling) & ... | `manim_tap_14_softmax_temperature.py` |
| `EP14_TemperatureDistortionScene` | [`TemperatureDistortionScene`](#ep14-temperaturedistortionscene) | 🧠 AI | 🎬 Động | `3` | Hàm Softmax Nhiệt Độ (Temperature Scaling) & ... | `manim_tap_14_softmax_temperature.py` |
| `EP14_TopKTopPSamplingScene` | [`TopKTopPSamplingScene`](#ep14-topktoppsamplingscene) | 🧠 AI | 🎬 Động | `3` | Hàm Softmax Nhiệt Độ (Temperature Scaling) & ... | `manim_tap_14_softmax_temperature.py` |
| `EP14_QuantumSuperpositionTextScene` | [`QuantumSuperpositionTextScene`](#ep14-quantumsuperpositiontextscene) | 🧠 AI | 🎬 Động | `4` | Hàm Softmax Nhiệt Độ (Temperature Scaling) & ... | `manim_tap_14_softmax_temperature.py` |
| `EP15_BayesTheoremEquationScene` | [`BayesTheoremEquationScene`](#ep15-bayestheoremequationscene) | 📐 Math | 🎬 Động | `4` | Quy Tắc Cập Nhật Suy Luận Bayes Liên Tục & Ph... | `manim_tap_15_bayesian_inference.py` |
| `EP15_BayesianBeliefUpdateLoopScene` | [`BayesianBeliefUpdateLoopScene`](#ep15-bayesianbeliefupdateloopscene) | 📐 Math | 🎬 Động | `5` | Quy Tắc Cập Nhật Suy Luận Bayes Liên Tục & Ph... | `manim_tap_15_bayesian_inference.py` |
| `EP15_MAPWeightDecayConnectionScene` | [`MAPWeightDecayConnectionScene`](#ep15-mapweightdecayconnectionscene) | 📐 Math | 🎬 Động | `4` | Quy Tắc Cập Nhật Suy Luận Bayes Liên Tục & Ph... | `manim_tap_15_bayesian_inference.py` |
| `EP15_BaseRateFallacyScene` | [`BaseRateFallacyScene`](#ep15-baseratefallacyscene) | 📐 Math | 🎬 Động | `4` | Quy Tắc Cập Nhật Suy Luận Bayes Liên Tục & Ph... | `manim_tap_15_bayesian_inference.py` |
| `EP16_SVDGeometricDecompositionScene` | [`SVDGeometricDecompositionScene`](#ep16-svdgeometricdecompositionscene) | 📐 Math | 🎬 Động | `6` | Phân Rã Giá Trị Kỳ Dị SVD & Nén Ma Trận Hạng ... | `manim_tap_16_svd_matrix_decomposition.py` |
| `EP16_LowRankApproximationScene` | [`LowRankApproximationScene`](#ep16-lowrankapproximationscene) | 📐 Math | 🎬 Động | `4` | Phân Rã Giá Trị Kỳ Dị SVD & Nén Ma Trận Hạng ... | `manim_tap_16_svd_matrix_decomposition.py` |
| `EP16_LoRAMatrixDecompositionScene` | [`LoRAMatrixDecompositionScene`](#ep16-loramatrixdecompositionscene) | 📐 Math | 🎬 Động | `3` | Phân Rã Giá Trị Kỳ Dị SVD & Nén Ma Trận Hạng ... | `manim_tap_16_svd_matrix_decomposition.py` |
| `EP17_AutoencoderBottleneckHourglassScene` | [`AutoencoderBottleneckHourglassScene`](#ep17-autoencoderbottleneckhourglassscene) | 🧠 AI | 🎬 Động | `4` | Không Gian Tiềm Ẩn Latent Space & Mô Hình Tự ... | `manim_tap_17_latent_space_autoencoders.py` |
| `EP17_SwissRollManifoldScene` | [`SwissRollManifoldScene`](#ep17-swissrollmanifoldscene) | 🧠 AI | 🎬 Động | `4` | Không Gian Tiềm Ẩn Latent Space & Mô Hình Tự ... | `manim_tap_17_latent_space_autoencoders.py` |
| `EP17_LatentSpaceVectorArithmeticScene` | [`LatentSpaceVectorArithmeticScene`](#ep17-latentspacevectorarithmeticscene) | 🧠 AI | 🎬 Động | `6` | Không Gian Tiềm Ẩn Latent Space & Mô Hình Tự ... | `manim_tap_17_latent_space_autoencoders.py` |
| `EP18_MonteCarloPiEstimationScene` | [`MonteCarloPiEstimationScene`](#ep18-montecarlopiestimationscene) | 📐 Math | 🎬 Động | `3` | Phương Pháp Lấy Mẫu Monte Carlo & Chuỗi Marko... | `manim_tap_18_monte_carlo_mcmc.py` |
| `EP18_MCMCRandomWalkLandscapeScene` | [`MCMCRandomWalkLandscapeScene`](#ep18-mcmcrandomwalklandscapescene) | 📐 Math | 🎬 Động | `6` | Phương Pháp Lấy Mẫu Monte Carlo & Chuỗi Marko... | `manim_tap_18_monte_carlo_mcmc.py` |
| `EP18_MonteCarloTreeSearchScene` | [`MonteCarloTreeSearchScene`](#ep18-montecarlotreesearchscene) | 📐 Math | 🎬 Động | `4` | Phương Pháp Lấy Mẫu Monte Carlo & Chuỗi Marko... | `manim_tap_18_monte_carlo_mcmc.py` |
| `EP19_NashEquilibriumSaddleScene` | [`NashEquilibriumSaddleScene`](#ep19-nashequilibriumsaddlescene) | 💻 CS | 🎬 Động | `4` | Lý Thuyết Trò Chơi & Cân Bằng Nash Không Hợp ... | `manim_tap_19_game_theory_nash.py` |
| `EP19_MinimaxAlphaBetaTreeScene` | [`MinimaxAlphaBetaTreeScene`](#ep19-minimaxalphabetatreescene) | 💻 CS | 🎬 Động | `5` | Lý Thuyết Trò Chơi & Cân Bằng Nash Không Hợp ... | `manim_tap_19_game_theory_nash.py` |
| `EP19_GANMinimaxGameScene` | [`GANMinimaxGameScene`](#ep19-ganminimaxgamescene) | 💻 CS | 🎬 Động | `3` | Lý Thuyết Trò Chơi & Cân Bằng Nash Không Hợp ... | `manim_tap_19_game_theory_nash.py` |
| `EP20_HessianMatrixCurvatureScene` | [`HessianMatrixCurvatureScene`](#ep20-hessianmatrixcurvaturescene) | 📐 Math | 🎬 Động | `5` | Ma Trận Hessian, Điểm Yên Ngựa Saddle Points ... | `manim_tap_20_hessian_saddle_points.py` |
| `EP20_DauphinExponentialSaddleScene` | [`DauphinExponentialSaddleScene`](#ep20-dauphinexponentialsaddlescene) | 📐 Math | 🎬 Động | `3` | Ma Trận Hessian, Điểm Yên Ngựa Saddle Points ... | `manim_tap_20_hessian_saddle_points.py` |
| `EP20_EscapingSaddleMomentumScene` | [`EscapingSaddleMomentumScene`](#ep20-escapingsaddlemomentumscene) | 📐 Math | 🎬 Động | `6` | Ma Trận Hessian, Điểm Yên Ngựa Saddle Points ... | `manim_tap_20_hessian_saddle_points.py` |
| `EP21_BatchNormTransformationScene` | [`BatchNormTransformationScene`](#ep21-batchnormtransformationscene) | 🧠 AI | 🎬 Động | `5` | Chuẩn Hóa Lô Batch Normalization & Kiểm Soát ... | `manim_tap_21_batch_normalization.py` |
| `EP21_SmoothingOptimizationLandscapeScene` | [`SmoothingOptimizationLandscapeScene`](#ep21-smoothingoptimizationlandscapescene) | 🧠 AI | 🎬 Động | `4` | Chuẩn Hóa Lô Batch Normalization & Kiểm Soát ... | `manim_tap_21_batch_normalization.py` |
| `EP21_BatchNormVsLayerNormTensorScene` | [`BatchNormVsLayerNormTensorScene`](#ep21-batchnormvslayernormtensorscene) | 🧠 AI | 🎬 Động | `6` | Chuẩn Hóa Lô Batch Normalization & Kiểm Soát ... | `manim_tap_21_batch_normalization.py` |
| `EP22_NonlinearFoldingSpaceScene` | [`NonlinearFoldingSpaceScene`](#ep22-nonlinearfoldingspacescene) | 🧠 AI | 🎬 Động | `4` | Định Lý Xấp Xỉ Phổ Quát & Các Hàm Kích Hoạt P... | `manim_tap_22_nonlinear_activations.py` |
| `EP22_ReLUvsGELUvsSwishScene` | [`ReLUvsGELUvsSwishScene`](#ep22-reluvsgeluvsswishscene) | 🧠 AI | 🎬 Động | `7` | Định Lý Xấp Xỉ Phổ Quát & Các Hàm Kích Hoạt P... | `manim_tap_22_nonlinear_activations.py` |
| `EP22_UniversalApproximationFoldScene` | [`UniversalApproximationFoldScene`](#ep22-universalapproximationfoldscene) | 🧠 AI | 🎬 Động | `5` | Định Lý Xấp Xỉ Phổ Quát & Các Hàm Kích Hoạt P... | `manim_tap_22_nonlinear_activations.py` |
| `EP23_ConvolutionSlidingWindowKernelScene` | [`ConvolutionSlidingWindowKernelScene`](#ep23-convolutionslidingwindowkernelscene) | 🧠 AI | 🎬 Động | `6` | Định Lý Tích Chập Fourier & Miền Tần Số Trong... | `manim_tap_23_convolution_fourier.py` |
| `EP23_FourierConvolutionTheoremDualScene` | [`FourierConvolutionTheoremDualScene`](#ep23-fourierconvolutiontheoremdualscene) | 🧠 AI | 🎬 Động | `5` | Định Lý Tích Chập Fourier & Miền Tần Số Trong... | `manim_tap_23_convolution_fourier.py` |
| `EP23_SpectralOperatorAndViTEvolutionScene` | [`SpectralOperatorAndViTEvolutionScene`](#ep23-spectraloperatorandvitevolutionscene) | 🧠 AI | 🎬 Động | `5` | Định Lý Tích Chập Fourier & Miền Tần Số Trong... | `manim_tap_23_convolution_fourier.py` |
| `EP24_CausalHierarchyLadderScene` | [`CausalHierarchyLadderScene`](#ep24-causalhierarchyladderscene) | 🧠 AI | 🎬 Động | `5` | Lý Thuyết Suy Luận Nhân Quả Causal Inference ... | `manim_tap_24_causal_inference.py` |
| `EP24_BackdoorCriterionGraphSurgeryScene` | [`BackdoorCriterionGraphSurgeryScene`](#ep24-backdoorcriteriongraphsurgeryscene) | 🧠 AI | 🎬 Động | `4` | Lý Thuyết Suy Luận Nhân Quả Causal Inference ... | `manim_tap_24_causal_inference.py` |
| `EP24_CounterfactualParallelWorldsScene` | [`CounterfactualParallelWorldsScene`](#ep24-counterfactualparallelworldsscene) | 🧠 AI | 🎬 Động | `4` | Lý Thuyết Suy Luận Nhân Quả Causal Inference ... | `manim_tap_24_causal_inference.py` |
| `EP25_GrandMathematicalTimelineScene` | [`GrandMathematicalTimelineScene`](#ep25-grandmathematicaltimelinescene) | 📐 Math | 🎬 Động | `4` | Đại Hợp Âm Toán Học AI & Triết Lý Đạo Làm Ngh... | `manim_tap_25_grand_mathematical_synthesis.py` |
| `EP25_UnifiedMathematicalCoreMatrixScene` | [`UnifiedMathematicalCoreMatrixScene`](#ep25-unifiedmathematicalcorematrixscene) | 📐 Math | 🎬 Động | `3` | Đại Hợp Âm Toán Học AI & Triết Lý Đạo Làm Ngh... | `manim_tap_25_grand_mathematical_synthesis.py` |
| `EP25_TheCraftsmanWayFinalSynthesisScene` | [`TheCraftsmanWayFinalSynthesisScene`](#ep25-thecraftsmanwayfinalsynthesisscene) | 📐 Math | 🎬 Động | `6` | Đại Hợp Âm Toán Học AI & Triết Lý Đạo Làm Ngh... | `manim_tap_25_grand_mathematical_synthesis.py` |
| `EP100_SplayDegenerateBSTScene` | [`SplayDegenerateBSTScene`](#ep100-splaydegeneratebstscene) | 💻 CS | 🎬 Động | `7` | Cấu Trúc Cây Tự Cân Bằng Splay Tree & Phân Tí... | `manim_tap_splay_tree.py` |
| `EP100_SplayRotationsScene` | [`SplayRotationsScene`](#ep100-splayrotationsscene) | 💻 CS | 🎬 Động | `6` | Cấu Trúc Cây Tự Cân Bằng Splay Tree & Phân Tí... | `manim_tap_splay_tree.py` |
| `EP100_SplayPotentialAmortizedScene` | [`SplayPotentialAmortizedScene`](#ep100-splaypotentialamortizedscene) | 💻 CS | 🎬 Động | `5` | Cấu Trúc Cây Tự Cân Bằng Splay Tree & Phân Tí... | `manim_tap_splay_tree.py` |
| `EP106_DuotoneShowcaseScene` | [`DuotoneShowcaseScene`](#ep106-duotoneshowcasescene) | 💻 CS | 🖼️ Tĩnh | `0` | Hệ Thống Icon Vector Phân Cấp & Thẻ Kiến Trúc... | `test_duotone_component.py` |
| `EP102_ChemistryWaterMoleculeScene` | [`ChemistryWaterMoleculeScene`](#ep102-chemistrywatermoleculescene) | 🧪 Chem | 🎬 Động | `6` | Cấu Trúc Không Gian Phân Tử, Mô Hình Lai Hóa ... | `template_chemistry.py` |
| `EP104_CSGraphDijkstraScene` | [`CSGraphDijkstraScene`](#ep104-csgraphdijkstrascene) | 💻 CS | 🎬 Động | `6` | Thuật Toán Tìm Đường Đi Ngắn Nhất Dijkstra & ... | `template_cs_algo.py` |
| `EP105_Math3B1BMatrixScene` | [`Math3B1BMatrixScene`](#ep105-math3b1bmatrixscene) | 📐 Math | 🎬 Động | `6` | Biến Đổi Ma Trận Tuyến Tính & Ý Nghĩa Hình Họ... | `template_math_3b1b.py` |
| `EP103_MLAttentionMechanismScene` | [`MLAttentionMechanismScene`](#ep103-mlattentionmechanismscene) | 🧠 AI | 🎬 Động | `4` | Cơ Chế Scaled Dot-Product Attention Ma Trận S... | `template_ml.py` |
| `EP101_PhysicsPendulumScene` | [`PhysicsPendulumScene`](#ep101-physicspendulumscene) | ⚡ Phys | 🎬 Động | `5` | Phương Trình Vi Phân Dao Động Điều Hòa & Bảo ... | `template_physics.py` |

---

## 3. Chi Tiết Từng Phân Cảnh (Detailed Registry Entries)

### 💻 KHOA HỌC MÁY TÍNH & GIẢI THUẬT (CS & DATA STRUCTURES)

#### `EP05_PRNGCycleModuloScene` — PRNGCycleModuloScene
- **Tập / Chủ đề**: Tập 05 — *TẬP 05: MÁY TÍNH CHƯA BAO GIỜ BIẾT "NGẪU NHIÊN" — ẢO TƯỞNG CỦA SỰ TỰ DO*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_05_prng_entropy.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_05_prng_entropy.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `6` | Thời lượng ước tính: `11.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Hàm Sinh Số Giả Ngẫu Nhiên PRNG & Entropy Mật Mã (Mersenne Twister / von Neumann)**
- **Kịch bản & Ngữ cảnh**: *"Scene 3: Modulo Arithmetic & The Closed Deterministic Cycle of PRNG
Shows LCG: X_{n+1} = (a * X_n + c) mod m"*
- **Công thức LaTeX cốt lõi**:
  - `$X_{n+1} = (a \cdot X_n + c) \pmod m$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_05_prng_entropy.py PRNGCycleModuloScene
  ```

#### `EP05_TemperatureSamplingScene` — TemperatureSamplingScene
- **Tập / Chủ đề**: Tập 05 — *TẬP 05: MÁY TÍNH CHƯA BAO GIỜ BIẾT "NGẪU NHIÊN" — ẢO TƯỞNG CỦA SỰ TỰ DO*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_05_prng_entropy.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_05_prng_entropy.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `6` | Thời lượng ước tính: `12.0s`
- **Căn cứ khoa học / Tiên đề toán học**: **Hàm Sinh Số Giả Ngẫu Nhiên PRNG & Entropy Mật Mã (Mersenne Twister / von Neumann)**
- **Kịch bản & Ngữ cảnh**: *"Scene 4: Softmax Temperature Sampling in AI & LLMs
P(w_i) = exp(z_i / T) / sum_j exp(z_j / T)"*
- **Công thức LaTeX cốt lõi**:
  - `$P(w_i) = \frac{e^{z_i / T}}{\sum_{j} e^{z_j / T}}$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_05_prng_entropy.py TemperatureSamplingScene
  ```

#### `EP05_PRNGCycleShortScene` — PRNGCycleShortScene
- **Tập / Chủ đề**: Tập 05 — *TẬP 05: MÁY TÍNH CHƯA BAO GIỜ BIẾT "NGẪU NHIÊN" — ẢO TƯỞNG CỦA SỰ TỰ DO*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_05_prng_entropy.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_05_prng_entropy.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `6` | Thời lượng ước tính: `11.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Hàm Sinh Số Giả Ngẫu Nhiên PRNG & Entropy Mật Mã (Mersenne Twister / von Neumann)**
- **Kịch bản & Ngữ cảnh**: *"Scene 2 for Short 30s: 9:16 Portrait (1080x1920)
Watermark UR, Vertical Modulo Circle & Temperature Insight"*
- **Công thức LaTeX cốt lõi**:
  - `$X_{n+1} = (aX_n + c) \pmod m$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_05_prng_entropy.py PRNGCycleShortScene
  ```

#### `EP13_ShannonEntropyCurveScene` — ShannonEntropyCurveScene
- **Tập / Chủ đề**: Tập 13 — *TÔI LÀM VIỆC — TẬP 13: BẢN CHẤT ENTROPY SHANNON & THƯỚC ĐO SỰ BẤT ĐỊNH CỦA CỖ MÁY*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_13_entropy_shannon.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_13_entropy_shannon.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `5` | Thời lượng ước tính: `11.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Thuyết Thông Tin & Entropy Shannon (Claude Shannon, 1948)**
- **Kịch bản & Ngữ cảnh**: *"Scene 2: Bernoulli Entropy Curve H(p) = -p log2(p) - (1-p) log2(1-p)."*
- **Công thức LaTeX cốt lõi**:
  - `$H(p) = -p \log_2(p) - (1-p) \log_2(1-p)$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_13_entropy_shannon.py ShannonEntropyCurveScene
  ```

#### `EP13_CrossEntropyLossScene` — CrossEntropyLossScene
- **Tập / Chủ đề**: Tập 13 — *TÔI LÀM VIỆC — TẬP 13: BẢN CHẤT ENTROPY SHANNON & THƯỚC ĐO SỰ BẤT ĐỊNH CỦA CỖ MÁY*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_13_entropy_shannon.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_13_entropy_shannon.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `4` | Thời lượng ước tính: `9.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Thuyết Thông Tin & Entropy Shannon (Claude Shannon, 1948)**
- **Kịch bản & Ngữ cảnh**: *"Scene 3: Cross-Entropy Loss between True Distribution P and Predicted Q."*
- **Công thức LaTeX cốt lõi**:
  - `$H(P, Q) = -\sum_{x} P(x) \log Q(x)$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_13_entropy_shannon.py CrossEntropyLossScene
  ```

#### `EP13_KLDivergenceScene` — KLDivergenceScene
- **Tập / Chủ đề**: Tập 13 — *TÔI LÀM VIỆC — TẬP 13: BẢN CHẤT ENTROPY SHANNON & THƯỚC ĐO SỰ BẤT ĐỊNH CỦA CỖ MÁY*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_13_entropy_shannon.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_13_entropy_shannon.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `4` | Thời lượng ước tính: `9.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Thuyết Thông Tin & Entropy Shannon (Claude Shannon, 1948)**
- **Kịch bản & Ngữ cảnh**: *"Scene 4: Decomposition H(P, Q) = H(P) + D_KL(P || Q)."*
- **Công thức LaTeX cốt lõi**:
  - `$H(P, Q) = H(P) + D_{KL}(P \parallel Q)$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_13_entropy_shannon.py KLDivergenceScene
  ```

#### `EP13_PerplexityBranchingScene` — PerplexityBranchingScene
- **Tập / Chủ đề**: Tập 13 — *TÔI LÀM VIỆC — TẬP 13: BẢN CHẤT ENTROPY SHANNON & THƯỚC ĐO SỰ BẤT ĐỊNH CỦA CỖ MÁY*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_13_entropy_shannon.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_13_entropy_shannon.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `6` | Thời lượng ước tính: `12.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Thuyết Thông Tin & Entropy Shannon (Claude Shannon, 1948)**
- **Kịch bản & Ngữ cảnh**: *"Scene 5: Perplexity PP = 2^H and Next-Token Branching Factor."*
- **Công thức LaTeX cốt lõi**:
  - `$PP = 2^{H(P, Q)}$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_13_entropy_shannon.py PerplexityBranchingScene
  ```

#### `EP19_NashEquilibriumSaddleScene` — NashEquilibriumSaddleScene
- **Tập / Chủ đề**: Tập 19 — *TÔI LÀM VIỆC — SHORT TẬP 19: LÝ THUYẾT TRÒ CHƠI & CÂN BẰNG NASH*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_19_game_theory_nash.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_19_game_theory_nash.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `4` | Thời lượng ước tính: `8.0s`
- **Căn cứ khoa học / Tiên đề toán học**: **Lý Thuyết Trò Chơi & Cân Bằng Nash Không Hợp Tác (John Nash, 1950)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–08s (Câu hỏi thách thức) • Hình ảnh: Hai vua cờ đối diện nhau trên bàn cờ tối tăm, đường lưới laser phát sáng kết nối hai quân cờ thành một ma trận quyết định. • Lời thoại: "Khi hai trí tu"*
- **Công thức LaTeX cốt lõi**:
  - `$\max_x \min_y f(x, y) = \min_y \max_x f(x, y)$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_19_game_theory_nash.py NashEquilibriumSaddleScene
  ```

#### `EP19_MinimaxAlphaBetaTreeScene` — MinimaxAlphaBetaTreeScene
- **Tập / Chủ đề**: Tập 19 — *TÔI LÀM VIỆC — SHORT TẬP 19: LÝ THUYẾT TRÒ CHƠI & CÂN BẰNG NASH*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_19_game_theory_nash.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_19_game_theory_nash.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `5` | Thời lượng ước tính: `9.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Lý Thuyết Trò Chơi & Cân Bằng Nash Không Hợp Tác (John Nash, 1950)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–08s (Câu hỏi thách thức) • Hình ảnh: Hai vua cờ đối diện nhau trên bàn cờ tối tăm, đường lưới laser phát sáng kết nối hai quân cờ thành một ma trận quyết định. • Lời thoại: "Khi hai trí tu"*
- **Công thức LaTeX cốt lõi**:
  - `$V(s) = \max_{a \in A} \min_{s' \in S} V(s')$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_19_game_theory_nash.py MinimaxAlphaBetaTreeScene
  ```

#### `EP19_GANMinimaxGameScene` — GANMinimaxGameScene
- **Tập / Chủ đề**: Tập 19 — *TÔI LÀM VIỆC — SHORT TẬP 19: LÝ THUYẾT TRÒ CHƠI & CÂN BẰNG NASH*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_19_game_theory_nash.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_19_game_theory_nash.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `3` | Thời lượng ước tính: `6.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Lý Thuyết Trò Chơi & Cân Bằng Nash Không Hợp Tác (John Nash, 1950)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–08s (Câu hỏi thách thức) • Hình ảnh: Hai vua cờ đối diện nhau trên bàn cờ tối tăm, đường lưới laser phát sáng kết nối hai quân cờ thành một ma trận quyết định. • Lời thoại: "Khi hai trí tu"*
- **Công thức LaTeX cốt lõi**:
  - `$z \sim \mathcal{N}(0, I)$`
  - `$x \sim p_{\text{data}}$`
  - `$\min_G \max_D V(D, G) = \mathbb{E}_{x}[\log D(x)] + \mathbb{E}_{z}[\log(1 - D(G(z)))]$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_19_game_theory_nash.py GANMinimaxGameScene
  ```

#### `EP100_SplayDegenerateBSTScene` — SplayDegenerateBSTScene
- **Tập / Chủ đề**: Tập 100 — *TÔI LÀM VIỆC — Splay Tree: Cây Nhị Phân Tự Tối Ưu Hóa & Hàm Thế Năng Tarjan*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_splay_tree.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_splay_tree.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `7` | Thời lượng ước tính: `12.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Cấu Trúc Cây Tự Cân Bằng Splay Tree & Phân Tích Chi Phí Khấu Hao Bằng Hàm Thế Năng (Robert Tarjan & Daniel Sleator, 1985)**
- **Components cao cấp sử dụng**: `BottomCalloutCard`, `ConceptBadge`, `EquationBox`, `PointCallout`, `StateTrackerBar`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_splay_tree.py SplayDegenerateBSTScene
  ```

#### `EP100_SplayRotationsScene` — SplayRotationsScene
- **Tập / Chủ đề**: Tập 100 — *TÔI LÀM VIỆC — Splay Tree: Cây Nhị Phân Tự Tối Ưu Hóa & Hàm Thế Năng Tarjan*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_splay_tree.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_splay_tree.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `6` | Thời lượng ước tính: `11.0s`
- **Căn cứ khoa học / Tiên đề toán học**: **Cấu Trúc Cây Tự Cân Bằng Splay Tree & Phân Tích Chi Phí Khấu Hao Bằng Hàm Thế Năng (Robert Tarjan & Daniel Sleator, 1985)**
- **Components cao cấp sử dụng**: `BottomCalloutCard`, `ConceptBadge`, `EquationBox`, `PointCallout`, `StateTrackerBar`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_splay_tree.py SplayRotationsScene
  ```

#### `EP100_SplayPotentialAmortizedScene` — SplayPotentialAmortizedScene
- **Tập / Chủ đề**: Tập 100 — *TÔI LÀM VIỆC — Splay Tree: Cây Nhị Phân Tự Tối Ưu Hóa & Hàm Thế Năng Tarjan*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_splay_tree.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_splay_tree.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `5` | Thời lượng ước tính: `9.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Cấu Trúc Cây Tự Cân Bằng Splay Tree & Phân Tích Chi Phí Khấu Hao Bằng Hàm Thế Năng (Robert Tarjan & Daniel Sleator, 1985)**
- **Công thức LaTeX cốt lõi**:
  - `$\text{Total Amortized} = \mathcal{O}(\log N)$`
  - `$\Phi(T) = \sum_{x \in T} \log_2(\text{size}(x))$`
- **Components cao cấp sử dụng**: `BottomCalloutCard`, `ConceptBadge`, `EquationBox`, `StateTrackerBar`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_splay_tree.py SplayPotentialAmortizedScene
  ```

#### `EP106_DuotoneShowcaseScene` — DuotoneShowcaseScene
- **Tập / Chủ đề**: Tập 106 — *Manim Asset Library — Phosphor Duotone Showcase (1,512 SVG Icons)*
- **Tệp nguồn**: [`assets/scripts_video/test_duotone_component.py`](file:////home/zen/hermes-agent/assets/scripts_video/test_duotone_component.py)
- **Tính chất**: `⚪ STATIC FRAME (Khung Hình Tĩnh)` | Animations: `0` | Thời lượng ước tính: `2.0s`
- **Căn cứ khoa học / Tiên đề toán học**: **Hệ Thống Icon Vector Phân Cấp & Thẻ Kiến Trúc Hệ Thống (Phosphor Duotone Standard)**
- **Components cao cấp sử dụng**: `ArchitectureNode`, `DuotoneBadge`, `DuotoneIcon`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/test_duotone_component.py DuotoneShowcaseScene
  ```

#### `EP104_CSGraphDijkstraScene` — CSGraphDijkstraScene
- **Tập / Chủ đề**: Tập 104 — *Manim Science — Thuật Toán: Đồ Thị Trọng Số & Tìm Đường Ngắn Nhất Dijkstra*
- **Tệp nguồn**: [`.agents/skills/manim-production/references/templates/template_cs_algo.py`](file:////home/zen/hermes-agent/.agents/skills/manim-production/references/templates/template_cs_algo.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `6` | Thời lượng ước tính: `11.0s`
- **Căn cứ khoa học / Tiên đề toán học**: **Thuật Toán Tìm Đường Đi Ngắn Nhất Dijkstra & Kỹ Thuật Relax Cạnh (Edsger W. Dijkstra, 1959)**
- **Công thức LaTeX cốt lõi**:
  - `$d[v] = \min(d[v], d[u] + w(u, v))$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/.agents/skills/manim-production/references/templates/template_cs_algo.py CSGraphDijkstraScene
  ```

### 🧠 TRÍ TUỆ NHÂN TẠO & DEEP LEARNING (AI / ML)

#### `EP01_CoinPhysicsScene` — CoinPhysicsScene
- **Tập / Chủ đề**: Tập 01 — *TẬP 01 SHORTS: ĐỒNG XU CỦA CỖ MÁY (TẠI SAO AI KHÔNG CHẮC CHẮN 100%?)*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_01_probability.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_01_probability.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `6` | Thời lượng ước tính: `11.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Định lý Bayes & Phân phối Xác suất Tiền nghiệm / Hậu nghiệm (Thomas Bayes, 1763)**
- **Kịch bản & Ngữ cảnh**: *"Scene 1: Cú búng tay và Quỹ đạo tất định
Bố cục 60/40:
- 60% bên trái: Không gian ném parabol vật lý, vector vận tốc & vận tốc góc GlowingArrow.
- 40% bên phải: Thẻ GlassCard HUD hiển thị hệ phương trình vi phân chuyển động.
SFX Cues:
- 0.5s: whoosh (búng tay phóng đồng xu)
- 1.5s: whoosh (quỹ đạo bay lên đỉnh)
- 3.5s: impact (tiếp đất & xác lập kết quả)
- 4.5s: shimmer (eureka: chân lý tất định)"*
- **Công thức LaTeX cốt lõi**:
  - `$\vec{v}_0$`
  - `$\vec{\omega}$`
  - `$y(t) = v_0 \sin(\theta)t - \frac{1}{2}gt^2$`
  - `$\theta_{\text{spin}}(t) = \omega_0 t + \alpha t^2$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_01_probability.py CoinPhysicsScene
  ```

#### `EP01_BayesianUpdateScene` — BayesianUpdateScene
- **Tập / Chủ đề**: Tập 01 — *TẬP 01 SHORTS: ĐỒNG XU CỦA CỖ MÁY (TẠI SAO AI KHÔNG CHẮC CHẮN 100%?)*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_01_probability.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_01_probability.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `6` | Thời lượng ước tính: `11.9s`
- **Căn cứ khoa học / Tiên đề toán học**: **Định lý Bayes & Phân phối Xác suất Tiền nghiệm / Hậu nghiệm (Thomas Bayes, 1763)**
- **Kịch bản & Ngữ cảnh**: *"Scene 2: Định lý Bayes — Cập nhật niềm tin
Bố cục 60/40:
- 60% bên trái: Đồ thị hàm mật độ xác suất dịch chuyển từ Prior sang Posterior khi có bằng chứng.
- 40% bên phải: Thẻ GlassCard HUD hiển thị Định lý Bayes & phân rã 3 thành tố.
SFX Cues:
- 0.5s: whoosh (vẽ đường cong Prior)
- 1.8s: pop (các điểm dữ liệu thực nghiệm rơi xuống)
- 3.5s: impact (công thức Bayes biến đổi sang Posterior)
- 5.2s: shimmer (hội tụ niềm tin vững chắc)"*
- **Công thức LaTeX cốt lõi**:
  - `$P(\theta \mid D) = \frac{P(D \mid \theta) \cdot P(\theta)}{P(D)}$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_01_probability.py BayesianUpdateScene
  ```

#### `EP01_AITokenProbabilityScene` — AITokenProbabilityScene
- **Tập / Chủ đề**: Tập 01 — *TẬP 01 SHORTS: ĐỒNG XU CỦA CỖ MÁY (TẠI SAO AI KHÔNG CHẮC CHẮN 100%?)*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_01_probability.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_01_probability.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `6` | Thời lượng ước tính: `12.4s`
- **Căn cứ khoa học / Tiên đề toán học**: **Định lý Bayes & Phân phối Xác suất Tiền nghiệm / Hậu nghiệm (Thomas Bayes, 1763)**
- **Kịch bản & Ngữ cảnh**: *"Scene 3: Next Token Prediction — Cỗ máy chọn từ theo phân phối Softmax
Bố cục Studio:
- Phía trên: Prompt HUD kính mờ gõ từng chữ.
- Phía dưới (60/40):
  - 60% bên trái: Đồ thị thanh xác suất Softmax co giãn động theo tỷ lệ %.
  - 40% bên phải: Thẻ GlassCard HUD chứa phương trình Softmax & nhiệt độ Temperature T.
SFX Cues:
- 0.5s: whoosh (prompt & hệ khung mở ra)
- 1.5s: pop (các thanh xác suất Softmax dâng lên)
- 3.2s: impact (chọn token 'Toán học')
- 4.5s: shimmer (hoàn tất câu đố trí tuệ nhân tạo)"*
- **Công thức LaTeX cốt lõi**:
  - `$P(w_i) = \frac{e^{z_i / T}}{\sum_{j=1}^V e^{z_j / T}}$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_01_probability.py AITokenProbabilityScene
  ```

#### `EP02_LossLandscape3DScene` — LossLandscape3DScene
- **Tập / Chủ đề**: Tập 02 — *KỊCH BẢN SHORT 30S: CỖ MÁY MÒ MẪM TRONG BÓNG TỐI?*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_02_gradient_descent.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_02_gradient_descent.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `3` | Thời lượng ước tính: `5.7s`
- **Căn cứ khoa học / Tiên đề toán học**: **Giải thuật Hạ Gradient Đa Chiều & Bề Mặt Hàm Mất Mát (Cauchy 1847, Robbins-Monro 1951)**
- **Kịch bản & Ngữ cảnh**: *"Phân cảnh 1: Không gian hàm mất mát 3D phi lồi & Hạt sáng mò mẫm trong bóng tối.
SFX Cues:
- 0.5s: whoosh (camera xoay vào không gian 3D)
- 1.8s: impact (hàm mất mát lộ diện trên HUD card)
- 3.5s: blip (hạt sáng bắt đầu trượt dốc)
- 5.5s: shimmer (chạm đáy cực tiểu cục bộ)"*
- **Công thức LaTeX cốt lõi**:
  - `$\mathcal{L}(\mathbf{w}) = \frac{1}{N}\sum_{i=1}^N \ell(f(x_i; \mathbf{w}), y_i)$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_02_gradient_descent.py LossLandscape3DScene
  ```

#### `EP02_GradientVectorFieldScene` — GradientVectorFieldScene
- **Tập / Chủ đề**: Tập 02 — *KỊCH BẢN SHORT 30S: CỖ MÁY MÒ MẪM TRONG BÓNG TỐI?*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_02_gradient_descent.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_02_gradient_descent.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `7` | Thời lượng ước tính: `12.4s`
- **Căn cứ khoa học / Tiên đề toán học**: **Giải thuật Hạ Gradient Đa Chiều & Bề Mặt Hàm Mất Mát (Cauchy 1847, Robbins-Monro 1951)**
- **Kịch bản & Ngữ cảnh**: *"Phân cảnh 2: Mặt phẳng tiếp diện & Vector Gradient trong không gian 2D/3D.
Bố cục 60/40:
- 60% bên trái: Đường đồng mức Elip & Vector tiếp tuyến GlowingArrow (Đỏ: dốc lên, Cyan: dốc xuống).
- 40% bên phải: Thẻ GlassCard HUD hiển thị quy tắc cập nhật tham số vi phân.
SFX Cues:
- 0.5s: whoosh (đường đồng mức vẽ ra)
- 1.8s: pop (điểm theta_t và vector dốc lên)
- 3.5s: impact (vector ngược dốc -nabla L và công thức)
- 5.0s: shimmer (hội tụ hướng tối ưu)"*
- **Công thức LaTeX cốt lõi**:
  - `$\theta_t$`
  - `$\nabla \mathcal{L}$`
  - `$-\nabla \mathcal{L}$`
  - `$\theta_{t+1} = \theta_t - \eta \cdot \nabla_\theta \mathcal{L}(\theta_t)$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_02_gradient_descent.py GradientVectorFieldScene
  ```

#### `EP02_LearningRateDilemmaScene` — LearningRateDilemmaScene
- **Tập / Chủ đề**: Tập 02 — *KỊCH BẢN SHORT 30S: CỖ MÁY MÒ MẪM TRONG BÓNG TỐI?*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_02_gradient_descent.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_02_gradient_descent.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `11` | Thời lượng ước tính: `18.8s`
- **Căn cứ khoa học / Tiên đề toán học**: **Giải thuật Hạ Gradient Đa Chiều & Bề Mặt Hàm Mất Mát (Cauchy 1847, Robbins-Monro 1951)**
- **Kịch bản & Ngữ cảnh**: *"Phân cảnh 3: Cơn ác mộng Learning Rate (Quá chậm vs Nổ Loss vs Tối ưu).
Bố cục 60/40:
- 60% bên trái: Parabol hàm mất mát và quỹ đạo nhảy của hạt qua 3 trường hợp.
- 40% bên phải: Thẻ GlassCard HUD hiển thị chẩn đoán trạng thái (Hội tụ / Nổ NaN).
SFX Cues:
- 0.5s: whoosh (vẽ parabol)
- 1.8s: pop (eta quá nhỏ: bò chậm chạp)
- 3.2s: impact (eta quá lớn: nổ Loss NaN)
- 4.8s: shimmer (eta tối ưu: hội tụ trơn tru)"*
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_02_gradient_descent.py LearningRateDilemmaScene
  ```

#### `EP02_OptimizerShowdownScene` — OptimizerShowdownScene
- **Tập / Chủ đề**: Tập 02 — *KỊCH BẢN SHORT 30S: CỖ MÁY MÒ MẪM TRONG BÓNG TỐI?*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_02_gradient_descent.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_02_gradient_descent.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `5` | Thời lượng ước tính: `9.0s`
- **Căn cứ khoa học / Tiên đề toán học**: **Giải thuật Hạ Gradient Đa Chiều & Bề Mặt Hàm Mất Mát (Cauchy 1847, Robbins-Monro 1951)**
- **Kịch bản & Ngữ cảnh**: *"Phân cảnh 4: Cuộc đua của các thuật toán: SGD vs Momentum vs Adam trong hẻm núi hẹp.
Bố cục 60/40:
- 60% bên trái: Hẻm núi Ravine 2D và đường đua của 3 quả cầu.
- 40% bên phải: Thẻ GlassCard HUD chú giải cơ chế của từng thuật toán.
SFX Cues:
- 0.5s: whoosh (hẻm núi và các tay đua xuất phát)
- 1.5s: blip (SGD rung lắc đập vào vách núi)
- 3.0s: whoosh (Momentum và Adam bứt phá)
- 4.5s: shimmer (Adam chạm đích cực tiểu hoàn hảo)"*
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_02_gradient_descent.py OptimizerShowdownScene
  ```

#### `EP02_BackpropComputationalGraphScene` — BackpropComputationalGraphScene
- **Tập / Chủ đề**: Tập 02 — *KỊCH BẢN SHORT 30S: CỖ MÁY MÒ MẪM TRONG BÓNG TỐI?*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_02_gradient_descent.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_02_gradient_descent.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `9` | Thời lượng ước tính: `15.7s`
- **Căn cứ khoa học / Tiên đề toán học**: **Giải thuật Hạ Gradient Đa Chiều & Bề Mặt Hàm Mất Mát (Cauchy 1847, Robbins-Monro 1951)**
- **Kịch bản & Ngữ cảnh**: *"Phân cảnh 5: Đồ thị tính toán & Lan truyền ngược (Forward vs Backward Pass).
Bố cục Studio:
- Phía trên: Đồ thị nút tính toán mạng nơ-ron với Forward (Cyan) và Backward (Magenta).
- Phía dưới: Thẻ GlassCard HUD hiển thị Định lý mắt xích Chain Rule hoàn chỉnh.
SFX Cues:
- 0.5s: pop (các nút mạng nơ-ron xuất hiện)
- 1.5s: whoosh (chiều thuận Forward Pass)
- 3.2s: impact (chiều ngược Backward Pass tính đạo hàm riêng)
- 5.0s: shimmer (định lý Chain Rule kết nối trọn vẹn)"*
- **Công thức LaTeX cốt lõi**:
  - `$x$`
  - `$z_1$`
  - `$a_1$`
  - `$\mathcal{L}$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_02_gradient_descent.py BackpropComputationalGraphScene
  ```

#### `EP03_VectorEmbeddingSpaceScene` — VectorEmbeddingSpaceScene
- **Tập / Chủ đề**: Tập 03 — *CHỮ NGHĨA BIẾN THÀNH TỌA ĐỘ — ĐẠI SỐ TUYẾN TÍNH & VECTOR AI*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_03_vector_embeddings.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_03_vector_embeddings.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `4` | Thời lượng ước tính: `10.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Không Gian Nhúng Vector & Phép Đo Khoảng Cách Cosine (Mikolov et al., 2013)**
- **Kịch bản & Ngữ cảnh**: *"Scene 3: 3D Universe of Word Embeddings in 1536-dim projected via PCA.
SFX Cues:
- 0.5s: whoosh (camera moves into 3D space)
- 1.2s: blip (cluster 1 Royalty spawns)
- 2.2s: blip (cluster 2 Tech spawns)
- 3.2s: blip (cluster 3 Emotion spawns)
- 5.0s: shimmer (constellation links glow)"*
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_03_vector_embeddings.py VectorEmbeddingSpaceScene
  ```

#### `EP03_VectorArithmeticScene` — VectorArithmeticScene
- **Tập / Chủ đề**: Tập 03 — *CHỮ NGHĨA BIẾN THÀNH TỌA ĐỘ — ĐẠI SỐ TUYẾN TÍNH & VECTOR AI*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_03_vector_embeddings.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_03_vector_embeddings.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `5` | Thời lượng ước tính: `12.3s`
- **Căn cứ khoa học / Tiên đề toán học**: **Không Gian Nhúng Vector & Phép Đo Khoảng Cách Cosine (Mikolov et al., 2013)**
- **Kịch bản & Ngữ cảnh**: *"Scene 4: Semantic Vector Arithmetic
SFX Cues:
- 0.5s: whoosh (axes appear)
- 1.5s: whoosh (King and Man vectors grow)
- 3.2s: pop (King - Man diff vector reveals)
- 4.5s: whoosh (Woman vector adds)
- 6.0s: impact (Queen vector snaps & formula writes)
- 6.5s: shimmer (Eureka flash fires)"*
- **Công thức LaTeX cốt lõi**:
  - `$\vec{v}_{\text{King}} - \vec{v}_{\text{Man}} + \vec{v}_{\text{Woman}} \approx \vec{v}_{\text{Queen}}$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_03_vector_embeddings.py VectorArithmeticScene
  ```

#### `EP03_CosineSimilarityScene` — CosineSimilarityScene
- **Tập / Chủ đề**: Tập 03 — *CHỮ NGHĨA BIẾN THÀNH TỌA ĐỘ — ĐẠI SỐ TUYẾN TÍNH & VECTOR AI*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_03_vector_embeddings.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_03_vector_embeddings.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `3` | Thời lượng ước tính: `7.8s`
- **Căn cứ khoa học / Tiên đề toán học**: **Không Gian Nhúng Vector & Phép Đo Khoảng Cách Cosine (Mikolov et al., 2013)**
- **Kịch bản & Ngữ cảnh**: *"Scene 5: Cosine Similarity and Dot Product with Live HUD Gauge
SFX Cues:
- 0.5s: whoosh (Vector A & Base Arc reveal)
- 1.5s: whoosh (Vector B appears)
- 2.8s: whoosh (Vector B starts rotating towards Vector A)
- 5.5s: shimmer (Cosine hits 0.98, Eureka flash fires!)
- 5.8s: impact (Status confirms maximum resonance)"*
- **Công thức LaTeX cốt lõi**:
  - `$\cos(\theta) = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\| \|\mathbf{v}\|}$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_03_vector_embeddings.py CosineSimilarityScene
  ```

#### `EP03_MatrixTransformationScene` — MatrixTransformationScene
- **Tập / Chủ đề**: Tập 03 — *CHỮ NGHĨA BIẾN THÀNH TỌA ĐỘ — ĐẠI SỐ TUYẾN TÍNH & VECTOR AI*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_03_vector_embeddings.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_03_vector_embeddings.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `2` | Thời lượng ước tính: `6.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Không Gian Nhúng Vector & Phép Đo Khoảng Cách Cosine (Mikolov et al., 2013)**
- **Kịch bản & Ngữ cảnh**: *"Scene 6: Matrix Multiplication as Space Warping
SFX Cues:
- 0.5s: whoosh (grid lines expand)
- 1.5s: impact (Matrix formula reveals in HUD)
- 2.8s: whoosh (continuous dimensional space morphing)
- 5.5s: shimmer (grid stabilizes)"*
- **Công thức LaTeX cốt lõi**:
  - `$W = \begin{bmatrix} 1.2 & 0.7 \\ 0.3 & 1.4 \end{bmatrix}$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_03_vector_embeddings.py MatrixTransformationScene
  ```

#### `EP03_AttentionProjectionScene` — AttentionProjectionScene
- **Tập / Chủ đề**: Tập 03 — *CHỮ NGHĨA BIẾN THÀNH TỌA ĐỘ — ĐẠI SỐ TUYẾN TÍNH & VECTOR AI*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_03_vector_embeddings.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_03_vector_embeddings.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `3` | Thời lượng ước tính: `7.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Không Gian Nhúng Vector & Phép Đo Khoảng Cách Cosine (Mikolov et al., 2013)**
- **Kịch bản & Ngữ cảnh**: *"Scene 7: Query - Key - Value Projections in Attention Mechanism
SFX Cues:
- 0.5s: pop (input token card appears)
- 1.8s: whoosh (3 projection rays shoot out)
- 2.8s: blip (Q, K, V target cards illuminate)
- 4.5s: impact (Attention formula reveals)
- 5.2s: shimmer (Attention score converges)"*
- **Công thức LaTeX cốt lõi**:
  - `$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_03_vector_embeddings.py AttentionProjectionScene
  ```

#### `EP03_OneHotVsEmbeddingScene` — OneHotVsEmbeddingScene
- **Tập / Chủ đề**: Tập 03 — *CHỮ NGHĨA BIẾN THÀNH TỌA ĐỘ — ĐẠI SỐ TUYẾN TÍNH & VECTOR AI*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_03_vector_embeddings_v2.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_03_vector_embeddings_v2.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `2` | Thời lượng ước tính: `5.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Không Gian Nhúng Vector & Phép Đo Khoảng Cách Cosine (Mikolov et al., 2013)**
- **Kịch bản & Ngữ cảnh**: *"So sánh trực giác giữa sự cô độc của One-Hot Encoding
và không gian liên kết ngữ nghĩa dày đặc của Vector Embeddings."*
- **Công thức LaTeX cốt lõi**:
  - `$\mathbf{v}_{\text{Mother}} = [0, 1, 0, \dots, 0]^T$`
  - `$\mathbf{v}_{\text{Family}} = [0, 0, 1, \dots, 0]^T$`
  - `$\mathbf{v}_{\text{Keyboard}} = [1, 0, 0, \dots, 0]^T$`
  - `$\mathbf{e}_{\text{Mother}} = [0.82, 0.65, -0.12, \dots]$`
- **Components cao cấp sử dụng**: `ComparisonPanel`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_03_vector_embeddings_v2.py OneHotVsEmbeddingScene
  ```

#### `EP03_VectorArithmeticKingQueen` — VectorArithmeticKingQueen
- **Tập / Chủ đề**: Tập 03 — *CHỮ NGHĨA BIẾN THÀNH TỌA ĐỘ — ĐẠI SỐ TUYẾN TÍNH & VECTOR AI*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_03_vector_embeddings_v2.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_03_vector_embeddings_v2.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `9` | Thời lượng ước tính: `17.0s`
- **Căn cứ khoa học / Tiên đề toán học**: **Không Gian Nhúng Vector & Phép Đo Khoảng Cách Cosine (Mikolov et al., 2013)**
- **Kịch bản & Ngữ cảnh**: *"Trực quan hóa hình học phép toán ngữ nghĩa kinh điển:
Vector(Vua) - Vector(Đàn ông) + Vector(Phụ nữ) = Vector(Nữ hoàng)
Sử dụng NeonArrow phát quang laser và safe_place chống đè chữ."*
- **Công thức LaTeX cốt lõi**:
  - `$\vec{v}_{\text{King}} - \vec{v}_{\text{Man}} + \vec{v}_{\text{Woman}} \approx \vec{v}_{\text{Queen}}$`
- **Components cao cấp sử dụng**: `DiagramCard`, `NeonArrow`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_03_vector_embeddings_v2.py VectorArithmeticKingQueen
  ```

#### `EP03_CosineSimilarityResonance` — CosineSimilarityResonance
- **Tập / Chủ đề**: Tập 03 — *CHỮ NGHĨA BIẾN THÀNH TỌA ĐỘ — ĐẠI SỐ TUYẾN TÍNH & VECTOR AI*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_03_vector_embeddings_v2.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_03_vector_embeddings_v2.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `7` | Thời lượng ước tính: `13.0s`
- **Căn cứ khoa học / Tiên đề toán học**: **Không Gian Nhúng Vector & Phép Đo Khoảng Cách Cosine (Mikolov et al., 2013)**
- **Kịch bản & Ngữ cảnh**: *"Trực quan hóa tích vô hướng và độ tương đồng Cosine:
Góc kẹp theta thu nhỏ lại khi hai ý niệm đồng điệu,
kèm theo bộ đếm thời gian thực AnimatedCounter."*
- **Components cao cấp sử dụng**: `EquationBox`, `NeonArrow`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_03_vector_embeddings_v2.py CosineSimilarityResonance
  ```

#### `EP07_MSEParabolaScene` — MSEParabolaScene
- **Tập / Chủ đề**: Tập 07 — *TẬP 07: THƯỚC ĐO NỖI ĐAU CỦA CỖ MÁY — HÀM MẤT MÁT LOSS FUNCTION*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_07_loss_function.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_07_loss_function.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `4` | Thời lượng ước tính: `7.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Hàm Mất Mát Cross-Entropy & Maximum Likelihood Estimation (Gauss, Fisher 1922)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–16s (Nỗi đau của silicon) • Hình ảnh: Màn hình terminal đêm muộn hiển thị các giá trị sai số đỏ rực nhấp nháy, kỹ sư im lặng theo dõi sự dao động của các tham số. • Lời thoại: "Con người h"*
- **Công thức LaTeX cốt lõi**:
  - `$\mathcal{L}_{\text{MSE}} = \frac{1}{n} \sum_{i=1}^n (y_i - \hat{y}_i)^2$`
  - `$\hat{y}_1 (\text{Error } = 2.2 \to \text{Loss } = 4.84)$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_07_loss_function.py MSEParabolaScene
  ```

#### `EP07_CrossEntropyLogCurveScene` — CrossEntropyLogCurveScene
- **Tập / Chủ đề**: Tập 07 — *TẬP 07: THƯỚC ĐO NỖI ĐAU CỦA CỖ MÁY — HÀM MẤT MÁT LOSS FUNCTION*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_07_loss_function.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_07_loss_function.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `4` | Thời lượng ước tính: `7.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Hàm Mất Mát Cross-Entropy & Maximum Likelihood Estimation (Gauss, Fisher 1922)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–16s (Nỗi đau của silicon) • Hình ảnh: Màn hình terminal đêm muộn hiển thị các giá trị sai số đỏ rực nhấp nháy, kỹ sư im lặng theo dõi sự dao động của các tham số. • Lời thoại: "Con người h"*
- **Công thức LaTeX cốt lõi**:
  - `$\mathcal{L}_{\text{CE}} = - \log(p_{\text{true}})$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_07_loss_function.py CrossEntropyLogCurveScene
  ```

#### `EP07_LossGradientVectorFlowScene` — LossGradientVectorFlowScene
- **Tập / Chủ đề**: Tập 07 — *TẬP 07: THƯỚC ĐO NỖI ĐAU CỦA CỖ MÁY — HÀM MẤT MÁT LOSS FUNCTION*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_07_loss_function.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_07_loss_function.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `3` | Thời lượng ước tính: `6.0s`
- **Căn cứ khoa học / Tiên đề toán học**: **Hàm Mất Mát Cross-Entropy & Maximum Likelihood Estimation (Gauss, Fisher 1922)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–16s (Nỗi đau của silicon) • Hình ảnh: Màn hình terminal đêm muộn hiển thị các giá trị sai số đỏ rực nhấp nháy, kỹ sư im lặng theo dõi sự dao động của các tham số. • Lời thoại: "Con người h"*
- **Công thức LaTeX cốt lõi**:
  - `$\frac{\partial \mathcal{L}}{\partial W_{ij}} = \frac{\partial \mathcal{L}}{\partial \hat{y}} \cdot \frac{\partial \hat{y}}{\partial z} \cdot \frac{\partial z}{\partial W_{ij}}$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_07_loss_function.py LossGradientVectorFlowScene
  ```

#### `EP07_LossConvergenceValleyScene` — LossConvergenceValleyScene
- **Tập / Chủ đề**: Tập 07 — *TẬP 07: THƯỚC ĐO NỖI ĐAU CỦA CỖ MÁY — HÀM MẤT MÁT LOSS FUNCTION*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_07_loss_function.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_07_loss_function.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `4` | Thời lượng ước tính: `7.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Hàm Mất Mát Cross-Entropy & Maximum Likelihood Estimation (Gauss, Fisher 1922)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–16s (Nỗi đau của silicon) • Hình ảnh: Màn hình terminal đêm muộn hiển thị các giá trị sai số đỏ rực nhấp nháy, kỹ sư im lặng theo dõi sự dao động của các tham số. • Lời thoại: "Con người h"*
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_07_loss_function.py LossConvergenceValleyScene
  ```

#### `EP08_ChainRuleGraphScene` — ChainRuleGraphScene
- **Tập / Chủ đề**: Tập 08 — *TẬP 08 SHORTS: DÒNG CHẢY NGƯỢC CỦA TRI THỨC*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_08_backpropagation.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_08_backpropagation.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `6` | Thời lượng ước tính: `11.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Thuật Toán Lan Truyền Ngược Backpropagation & Quy Tắc Đạo Hàm Chuỗi (Rumelhart, Hinton, Williams 1986)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–07s (The Paradox Hook) • Hình ảnh: Mạng nơ-ron phát sáng trong đêm, xung năng lượng đỏ bắn ngược từ Output về Input. • Lời thoại: "Mỗi khi trí tuệ nhân tạo dự đoán sai, hàng tỷ tham số làm"*
- **Công thức LaTeX cốt lõi**:
  - `$\frac{\partial L}{\partial w}$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_08_backpropagation.py ChainRuleGraphScene
  ```

#### `EP08_BackpropMultiLayerFlowScene` — BackpropMultiLayerFlowScene
- **Tập / Chủ đề**: Tập 08 — *TẬP 08 SHORTS: DÒNG CHẢY NGƯỢC CỦA TRI THỨC*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_08_backpropagation.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_08_backpropagation.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `9` | Thời lượng ước tính: `15.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Thuật Toán Lan Truyền Ngược Backpropagation & Quy Tắc Đạo Hàm Chuỗi (Rumelhart, Hinton, Williams 1986)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–07s (The Paradox Hook) • Hình ảnh: Mạng nơ-ron phát sáng trong đêm, xung năng lượng đỏ bắn ngược từ Output về Input. • Lời thoại: "Mỗi khi trí tuệ nhân tạo dự đoán sai, hàng tỷ tham số làm"*
- **Công thức LaTeX cốt lõi**:
  - `$w_{ij} \leftarrow w_{ij} - \eta \cdot \frac{\partial L}{\partial w_{ij}}$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_08_backpropagation.py BackpropMultiLayerFlowScene
  ```

#### `EP08_VanishingExplodingGradientScene` — VanishingExplodingGradientScene
- **Tập / Chủ đề**: Tập 08 — *TẬP 08 SHORTS: DÒNG CHẢY NGƯỢC CỦA TRI THỨC*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_08_backpropagation.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_08_backpropagation.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `4` | Thời lượng ước tính: `8.2s`
- **Căn cứ khoa học / Tiên đề toán học**: **Thuật Toán Lan Truyền Ngược Backpropagation & Quy Tắc Đạo Hàm Chuỗi (Rumelhart, Hinton, Williams 1986)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–07s (The Paradox Hook) • Hình ảnh: Mạng nơ-ron phát sáng trong đêm, xung năng lượng đỏ bắn ngược từ Output về Input. • Lời thoại: "Mỗi khi trí tuệ nhân tạo dự đoán sai, hàng tỷ tham số làm"*
- **Công thức LaTeX cốt lõi**:
  - `$\sigma'(x) \le 0.25$`
  - `$0.25 \times 0.25 \dots = 0.25^{10}$`
  - `$\approx 0.00000095 \to 0$`
  - `$f'(x) = 1 \quad (x > 0) \implies \text{Gradient Preserved!}$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_08_backpropagation.py VanishingExplodingGradientScene
  ```

#### `EP08_AutogradComputationalGraphScene` — AutogradComputationalGraphScene
- **Tập / Chủ đề**: Tập 08 — *TẬP 08 SHORTS: DÒNG CHẢY NGƯỢC CỦA TRI THỨC*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_08_backpropagation.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_08_backpropagation.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `5` | Thời lượng ước tính: `9.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Thuật Toán Lan Truyền Ngược Backpropagation & Quy Tắc Đạo Hàm Chuỗi (Rumelhart, Hinton, Williams 1986)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–07s (The Paradox Hook) • Hình ảnh: Mạng nơ-ron phát sáng trong đêm, xung năng lượng đỏ bắn ngược từ Output về Input. • Lời thoại: "Mỗi khi trí tuệ nhân tạo dự đoán sai, hàng tỷ tham số làm"*
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_08_backpropagation.py AutogradComputationalGraphScene
  ```

#### `EP09_OverfittingCurveClashScene` — OverfittingCurveClashScene
- **Tập / Chủ đề**: Tập 09 — *TÔI LÀM VIỆC — TẬP 09: NGHỆ THUẬT BUÔNG BỎ ĐỂ CỖ MÁY THÔNG THÁI (OVERFITTING & REGULARIZATION)*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_09_overfitting.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_09_overfitting.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `5` | Thời lượng ước tính: `9.7s`
- **Căn cứ khoa học / Tiên đề toán học**: **Hiện Tượng Quá Khớp Overfitting & Đánh Đổi Độ Chệch-Phương Sai (Bias-Variance Tradeoff)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–18s (Cạm bẫy của sự hoàn hảo) • Hình ảnh: Màn hình terminal đêm muộn, đồ thị Training Loss giảm về 0 tuyệt đối nhưng Validation Loss bùng nổ vọt lên trời cao. • Lời thoại: "Một cỗ máy đạt "*
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_09_overfitting.py OverfittingCurveClashScene
  ```

#### `EP09_L2RegularizationConstraintScene` — L2RegularizationConstraintScene
- **Tập / Chủ đề**: Tập 09 — *TÔI LÀM VIỆC — TẬP 09: NGHỆ THUẬT BUÔNG BỎ ĐỂ CỖ MÁY THÔNG THÁI (OVERFITTING & REGULARIZATION)*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_09_overfitting.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_09_overfitting.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `6` | Thời lượng ước tính: `11.2s`
- **Căn cứ khoa học / Tiên đề toán học**: **Hiện Tượng Quá Khớp Overfitting & Đánh Đổi Độ Chệch-Phương Sai (Bias-Variance Tradeoff)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–18s (Cạm bẫy của sự hoàn hảo) • Hình ảnh: Màn hình terminal đêm muộn, đồ thị Training Loss giảm về 0 tuyệt đối nhưng Validation Loss bùng nổ vọt lên trời cao. • Lời thoại: "Một cỗ máy đạt "*
- **Công thức LaTeX cốt lõi**:
  - `$w_1$`
  - `$\|w\|_2^2 \le C$`
  - `$w^* \text{ (Unconstrained)}$`
  - `$w^*_{L2} \text{ (Shrunk)}$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_09_overfitting.py L2RegularizationConstraintScene
  ```

#### `EP09_L1RegularizationDiamondScene` — L1RegularizationDiamondScene
- **Tập / Chủ đề**: Tập 09 — *TÔI LÀM VIỆC — TẬP 09: NGHỆ THUẬT BUÔNG BỎ ĐỂ CỖ MÁY THÔNG THÁI (OVERFITTING & REGULARIZATION)*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_09_overfitting.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_09_overfitting.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `5` | Thời lượng ước tính: `9.7s`
- **Căn cứ khoa học / Tiên đề toán học**: **Hiện Tượng Quá Khớp Overfitting & Đánh Đổi Độ Chệch-Phương Sai (Bias-Variance Tradeoff)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–18s (Cạm bẫy của sự hoàn hảo) • Hình ảnh: Màn hình terminal đêm muộn, đồ thị Training Loss giảm về 0 tuyệt đối nhưng Validation Loss bùng nổ vọt lên trời cao. • Lời thoại: "Một cỗ máy đạt "*
- **Công thức LaTeX cốt lõi**:
  - `$\|w\|_1 \le C$`
  - `$w_1 = 0 \quad (\text{Feature Pruned!})$`
  - `$\mathcal{L} = \mathcal{L}_0 + \lambda \sum_{i} |w_i|$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_09_overfitting.py L1RegularizationDiamondScene
  ```

#### `EP09_DropoutNetworkSparsityScene` — DropoutNetworkSparsityScene
- **Tập / Chủ đề**: Tập 09 — *TÔI LÀM VIỆC — TẬP 09: NGHỆ THUẬT BUÔNG BỎ ĐỂ CỖ MÁY THÔNG THÁI (OVERFITTING & REGULARIZATION)*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_09_overfitting.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_09_overfitting.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `6` | Thời lượng ước tính: `11.2s`
- **Căn cứ khoa học / Tiên đề toán học**: **Hiện Tượng Quá Khớp Overfitting & Đánh Đổi Độ Chệch-Phương Sai (Bias-Variance Tradeoff)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–18s (Cạm bẫy của sự hoàn hảo) • Hình ảnh: Màn hình terminal đêm muộn, đồ thị Training Loss giảm về 0 tuyệt đối nhưng Validation Loss bùng nổ vọt lên trời cao. • Lời thoại: "Một cỗ máy đạt "*
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_09_overfitting.py DropoutNetworkSparsityScene
  ```

#### `EP11_QKVProjectionScene` — QKVProjectionScene
- **Tập / Chủ đề**: Tập 11 — *TÔI LÀM VIỆC — TẬP 11: CƠ CHẾ CHÚ Ý ATTENTION & MA TRẬN QUERY-KEY-VALUE*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_11_attention_qkv.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_11_attention_qkv.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `4` | Thời lượng ước tính: `8.2s`
- **Căn cứ khoa học / Tiên đề toán học**: **Cơ Chế Scaled Dot-Product Attention (Query, Key, Value) (Vaswani et al., 2017)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–22s (Sự kiệt sức của mạng tuần hoàn RNN) • Hình ảnh: Chuỗi nơ-ron RNN truyền thông tin qua từng mắt xích thời gian, gradient teo tóp dần và thông tin bị xóa mờ sau vài chục từ. • Lời thoại"*
- **Công thức LaTeX cốt lõi**:
  - `$\mathbf{x} \ (\text{Input Token})$`
  - `$\times \mathbf{W}_Q$`
  - `$\times \mathbf{W}_K$`
  - `$\times \mathbf{W}_V$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_11_attention_qkv.py QKVProjectionScene
  ```

#### `EP11_AttentionHeatmapClashScene` — AttentionHeatmapClashScene
- **Tập / Chủ đề**: Tập 11 — *TÔI LÀM VIỆC — TẬP 11: CƠ CHẾ CHÚ Ý ATTENTION & MA TRẬN QUERY-KEY-VALUE*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_11_attention_qkv.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_11_attention_qkv.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `4` | Thời lượng ước tính: `8.2s`
- **Căn cứ khoa học / Tiên đề toán học**: **Cơ Chế Scaled Dot-Product Attention (Query, Key, Value) (Vaswani et al., 2017)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–22s (Sự kiệt sức của mạng tuần hoàn RNN) • Hình ảnh: Chuỗi nơ-ron RNN truyền thông tin qua từng mắt xích thời gian, gradient teo tóp dần và thông tin bị xóa mờ sau vài chục từ. • Lời thoại"*
- **Công thức LaTeX cốt lõi**:
  - `$\text{Attention}(\mathbf{Q}, \mathbf{K}, \mathbf{V}) = \text{softmax}\left(\frac{\mathbf{Q}\mathbf{K}^T}{\sqrt{d_k}}\right) \mathbf{V}$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_11_attention_qkv.py AttentionHeatmapClashScene
  ```

#### `EP11_WeightedValueSumScene` — WeightedValueSumScene
- **Tập / Chủ đề**: Tập 11 — *TÔI LÀM VIỆC — TẬP 11: CƠ CHẾ CHÚ Ý ATTENTION & MA TRẬN QUERY-KEY-VALUE*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_11_attention_qkv.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_11_attention_qkv.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `4` | Thời lượng ước tính: `8.2s`
- **Căn cứ khoa học / Tiên đề toán học**: **Cơ Chế Scaled Dot-Product Attention (Query, Key, Value) (Vaswani et al., 2017)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–22s (Sự kiệt sức của mạng tuần hoàn RNN) • Hình ảnh: Chuỗi nơ-ron RNN truyền thông tin qua từng mắt xích thời gian, gradient teo tóp dần và thông tin bị xóa mờ sau vài chục từ. • Lời thoại"*
- **Công thức LaTeX cốt lõi**:
  - `$0.72 \times \mathbf{v}_1$`
  - `$0.18 \times \mathbf{v}_2$`
  - `$0.10 \times \mathbf{v}_3$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_11_attention_qkv.py WeightedValueSumScene
  ```

#### `EP11_MultiHeadAttentionPrismScene` — MultiHeadAttentionPrismScene
- **Tập / Chủ đề**: Tập 11 — *TÔI LÀM VIỆC — TẬP 11: CƠ CHẾ CHÚ Ý ATTENTION & MA TRẬN QUERY-KEY-VALUE*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_11_attention_qkv.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_11_attention_qkv.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `5` | Thời lượng ước tính: `9.7s`
- **Căn cứ khoa học / Tiên đề toán học**: **Cơ Chế Scaled Dot-Product Attention (Query, Key, Value) (Vaswani et al., 2017)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–22s (Sự kiệt sức của mạng tuần hoàn RNN) • Hình ảnh: Chuỗi nơ-ron RNN truyền thông tin qua từng mắt xích thời gian, gradient teo tóp dần và thông tin bị xóa mờ sau vài chục từ. • Lời thoại"*
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_11_attention_qkv.py MultiHeadAttentionPrismScene
  ```

#### `EP12_PositionalEncodingWaveScene` — PositionalEncodingWaveScene
- **Tập / Chủ đề**: Tập 12 — *TÔI LÀM VIỆC — TẬP 12: KIẾN TRÚC TRANSFORMER & SỰ SỤP ĐỔ CỦA KHÔNG GIAN THỜI GIAN*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_12_transformer_architecture.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_12_transformer_architecture.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `5` | Thời lượng ước tính: `9.7s`
- **Căn cứ khoa học / Tiên đề toán học**: **Kiến Trúc Transformer Toàn Phần: Multi-Head Attention & Feed-Forward (Attention Is All You Need, 2017)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–22s (Cái chết của tính tuần tự thời gian) • Hình ảnh: Đồng hồ cát rơi từng hạt cát tuần tự chậm chạp, đột nhiên vỡ vụn biến thành một ma trận siêu liên kết song song toàn phần. • Lời thoại"*
- **Công thức LaTeX cốt lõi**:
  - `$\omega_0 \ (\text{Low Freq})$`
  - `$\omega_k \ (\text{High Freq})$`
  - `$\text{PE}_{(pos, 2i)} = \sin\left(\frac{pos}{10000^{2i/d}}\right), \quad \text{PE}_{(pos, 2i+1)} = \cos\left(\frac{pos}{10000^{2i/d}}\right)$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_12_transformer_architecture.py PositionalEncodingWaveScene
  ```

#### `EP12_TransformerBlockResidualScene` — TransformerBlockResidualScene
- **Tập / Chủ đề**: Tập 12 — *TÔI LÀM VIỆC — TẬP 12: KIẾN TRÚC TRANSFORMER & SỰ SỤP ĐỔ CỦA KHÔNG GIAN THỜI GIAN*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_12_transformer_architecture.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_12_transformer_architecture.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `7` | Thời lượng ước tính: `12.7s`
- **Căn cứ khoa học / Tiên đề toán học**: **Kiến Trúc Transformer Toàn Phần: Multi-Head Attention & Feed-Forward (Attention Is All You Need, 2017)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–22s (Cái chết của tính tuần tự thời gian) • Hình ảnh: Đồng hồ cát rơi từng hạt cát tuần tự chậm chạp, đột nhiên vỡ vụn biến thành một ma trận siêu liên kết song song toàn phần. • Lời thoại"*
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_12_transformer_architecture.py TransformerBlockResidualScene
  ```

#### `EP12_FeedForwardMemoryScene` — FeedForwardMemoryScene
- **Tập / Chủ đề**: Tập 12 — *TÔI LÀM VIỆC — TẬP 12: KIẾN TRÚC TRANSFORMER & SỰ SỤP ĐỔ CỦA KHÔNG GIAN THỜI GIAN*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_12_transformer_architecture.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_12_transformer_architecture.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `5` | Thời lượng ước tính: `9.7s`
- **Căn cứ khoa học / Tiên đề toán học**: **Kiến Trúc Transformer Toàn Phần: Multi-Head Attention & Feed-Forward (Attention Is All You Need, 2017)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–22s (Cái chết của tính tuần tự thời gian) • Hình ảnh: Đồng hồ cát rơi từng hạt cát tuần tự chậm chạp, đột nhiên vỡ vụn biến thành một ma trận siêu liên kết song song toàn phần. • Lời thoại"*
- **Công thức LaTeX cốt lõi**:
  - `$\times \mathbf{W}_1 + \mathbf{b}_1$`
  - `$\times \mathbf{W}_2 + \mathbf{b}_2$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_12_transformer_architecture.py FeedForwardMemoryScene
  ```

#### `EP12_ScalingLawEmergenceScene` — ScalingLawEmergenceScene
- **Tập / Chủ đề**: Tập 12 — *TÔI LÀM VIỆC — TẬP 12: KIẾN TRÚC TRANSFORMER & SỰ SỤP ĐỔ CỦA KHÔNG GIAN THỜI GIAN*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_12_transformer_architecture.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_12_transformer_architecture.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `5` | Thời lượng ước tính: `9.7s`
- **Căn cứ khoa học / Tiên đề toán học**: **Kiến Trúc Transformer Toàn Phần: Multi-Head Attention & Feed-Forward (Attention Is All You Need, 2017)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–22s (Cái chết của tính tuần tự thời gian) • Hình ảnh: Đồng hồ cát rơi từng hạt cát tuần tự chậm chạp, đột nhiên vỡ vụn biến thành một ma trận siêu liên kết song song toàn phần. • Lời thoại"*
- **Công thức LaTeX cốt lõi**:
  - `$L(N) \propto N^{-\alpha}$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_12_transformer_architecture.py ScalingLawEmergenceScene
  ```

#### `EP14_SoftmaxVectorTransformScene` — SoftmaxVectorTransformScene
- **Tập / Chủ đề**: Tập 14 — *TÔI LÀM VIỆC — SHORT TẬP 14: TẠI SAO AI CẦN MỘT CHÚT 'SỐT' ĐỂ SÁNG TẠO? NHIỆT ĐỘ SOFTMAX*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_14_softmax_temperature.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_14_softmax_temperature.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `6` | Thời lượng ước tính: `12.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Hàm Softmax Nhiệt Độ (Temperature Scaling) & Hiệu Chuẩn Xác Suất Mô Hình (Guo et al., 2017)**
- **Kịch bản & Ngữ cảnh**: *"Scene 2: Transforming raw logits z into valid probabilities sum = 1."*
- **Công thức LaTeX cốt lõi**:
  - `$\sigma(z)_i = \frac{e^{z_i}}{\sum_{j=1}^{K} e^{z_j}}$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_14_softmax_temperature.py SoftmaxVectorTransformScene
  ```

#### `EP14_TemperatureDistortionScene` — TemperatureDistortionScene
- **Tập / Chủ đề**: Tập 14 — *TÔI LÀM VIỆC — SHORT TẬP 14: TẠI SAO AI CẦN MỘT CHÚT 'SỐT' ĐỂ SÁNG TẠO? NHIỆT ĐỘ SOFTMAX*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_14_softmax_temperature.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_14_softmax_temperature.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `3` | Thời lượng ước tính: `6.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Hàm Softmax Nhiệt Độ (Temperature Scaling) & Hiệu Chuẩn Xác Suất Mô Hình (Guo et al., 2017)**
- **Kịch bản & Ngữ cảnh**: *"Scene 3: Modulating temperature T: Greedy (T->0), Balanced (T=1), Random (T->inf)."*
- **Công thức LaTeX cốt lõi**:
  - `$\sigma(z, T)_i = \frac{e^{z_i / T}}{\sum_{j} e^{z_j / T}}$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_14_softmax_temperature.py TemperatureDistortionScene
  ```

#### `EP14_TopKTopPSamplingScene` — TopKTopPSamplingScene
- **Tập / Chủ đề**: Tập 14 — *TÔI LÀM VIỆC — SHORT TẬP 14: TẠI SAO AI CẦN MỘT CHÚT 'SỐT' ĐỂ SÁNG TẠO? NHIỆT ĐỘ SOFTMAX*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_14_softmax_temperature.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_14_softmax_temperature.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `3` | Thời lượng ước tính: `6.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Hàm Softmax Nhiệt Độ (Temperature Scaling) & Hiệu Chuẩn Xác Suất Mô Hình (Guo et al., 2017)**
- **Kịch bản & Ngữ cảnh**: *"Scene 4: Top-K and Top-P (Nucleus) Sampling cutting off the long tail."*
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_14_softmax_temperature.py TopKTopPSamplingScene
  ```

#### `EP14_QuantumSuperpositionTextScene` — QuantumSuperpositionTextScene
- **Tập / Chủ đề**: Tập 14 — *TÔI LÀM VIỆC — SHORT TẬP 14: TẠI SAO AI CẦN MỘT CHÚT 'SỐT' ĐỂ SÁNG TẠO? NHIỆT ĐỘ SOFTMAX*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_14_softmax_temperature.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_14_softmax_temperature.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `4` | Thời lượng ước tính: `9.2s`
- **Căn cứ khoa học / Tiên đề toán học**: **Hàm Softmax Nhiệt Độ (Temperature Scaling) & Hiệu Chuẩn Xác Suất Mô Hình (Guo et al., 2017)**
- **Kịch bản & Ngữ cảnh**: *"Scene 5: Wavefunction collapse from cloud of probabilities into one token."*
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_14_softmax_temperature.py QuantumSuperpositionTextScene
  ```

#### `EP17_AutoencoderBottleneckHourglassScene` — AutoencoderBottleneckHourglassScene
- **Tập / Chủ đề**: Tập 17 — *TÔI LÀM VIỆC — SHORT TẬP 17: KHÔNG GIAN LATENT SPACE & AUTOENCODERS*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_17_latent_space_autoencoders.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_17_latent_space_autoencoders.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `4` | Thời lượng ước tính: `8.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Không Gian Tiềm Ẩn Latent Space & Mô Hình Tự Mã Hóa Autoencoder (Rumelhart 1986, Kingma 2013)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–08s (Câu hỏi thách thức) • Hình ảnh: Chiếc đồng hồ cát Autoencoder phát sáng neon, nén hình ảnh khuôn mặt qua một nút thắt cổ chai hẹp Latent Space. • Lời thoại: "Làm sao AI có thể hiểu đư"*
- **Công thức LaTeX cốt lõi**:
  - `$z \in \mathbb{R}^d$`
  - `$\mathcal{L}(x, \hat{x}) = \|x - g(f(x))\|^2$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_17_latent_space_autoencoders.py AutoencoderBottleneckHourglassScene
  ```

#### `EP17_SwissRollManifoldScene` — SwissRollManifoldScene
- **Tập / Chủ đề**: Tập 17 — *TÔI LÀM VIỆC — SHORT TẬP 17: KHÔNG GIAN LATENT SPACE & AUTOENCODERS*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_17_latent_space_autoencoders.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_17_latent_space_autoencoders.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `4` | Thời lượng ước tính: `8.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Không Gian Tiềm Ẩn Latent Space & Mô Hình Tự Mã Hóa Autoencoder (Rumelhart 1986, Kingma 2013)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–08s (Câu hỏi thách thức) • Hình ảnh: Chiếc đồng hồ cát Autoencoder phát sáng neon, nén hình ảnh khuôn mặt qua một nút thắt cổ chai hẹp Latent Space. • Lời thoại: "Làm sao AI có thể hiểu đư"*
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_17_latent_space_autoencoders.py SwissRollManifoldScene
  ```

#### `EP17_LatentSpaceVectorArithmeticScene` — LatentSpaceVectorArithmeticScene
- **Tập / Chủ đề**: Tập 17 — *TÔI LÀM VIỆC — SHORT TẬP 17: KHÔNG GIAN LATENT SPACE & AUTOENCODERS*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_17_latent_space_autoencoders.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_17_latent_space_autoencoders.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `6` | Thời lượng ước tính: `12.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Không Gian Tiềm Ẩn Latent Space & Mô Hình Tự Mã Hóa Autoencoder (Rumelhart 1986, Kingma 2013)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–08s (Câu hỏi thách thức) • Hình ảnh: Chiếc đồng hồ cát Autoencoder phát sáng neon, nén hình ảnh khuôn mặt qua một nút thắt cổ chai hẹp Latent Space. • Lời thoại: "Làm sao AI có thể hiểu đư"*
- **Công thức LaTeX cốt lõi**:
  - `$z_{\text{smiling}} = z_{\text{neutral}} + \vec{v}_{\text{smile}}$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_17_latent_space_autoencoders.py LatentSpaceVectorArithmeticScene
  ```

#### `EP21_BatchNormTransformationScene` — BatchNormTransformationScene
- **Tập / Chủ đề**: Tập 21 — *TÔI LÀM VIỆC — SHORT TẬP 21: BATCH NORMALIZATION & CÂN BẰNG GRADIENT*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_21_batch_normalization.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_21_batch_normalization.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `5` | Thời lượng ước tính: `9.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Chuẩn Hóa Lô Batch Normalization & Kiểm Soát Internal Covariate Shift (Ioffe & Szegedy, 2015)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–08s (Câu hỏi thách thức) • Hình ảnh: Dòng chảy gradient rực lửa bùng nổ xé toạc các tầng mạng nơ-ron sâu, các con số rung lắc mất kiểm soát trong không gian tối. • Lời thoại: "Khi một mạng"*
- **Công thức LaTeX cốt lõi**:
  - `$\mu_B = \frac{1}{m} \sum_{i=1}^m x_i$`
  - `$\sigma_B^2 = \frac{1}{m} \sum_{i=1}^m (x_i - \mu_B)^2$`
  - `$\hat{x}_i = \frac{x_i - \mu_B}{\sqrt{\sigma_B^2 + \epsilon}}$`
  - `$y_i = \gamma \hat{x}_i + \beta$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_21_batch_normalization.py BatchNormTransformationScene
  ```

#### `EP21_SmoothingOptimizationLandscapeScene` — SmoothingOptimizationLandscapeScene
- **Tập / Chủ đề**: Tập 21 — *TÔI LÀM VIỆC — SHORT TẬP 21: BATCH NORMALIZATION & CÂN BẰNG GRADIENT*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_21_batch_normalization.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_21_batch_normalization.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `4` | Thời lượng ước tính: `8.0s`
- **Căn cứ khoa học / Tiên đề toán học**: **Chuẩn Hóa Lô Batch Normalization & Kiểm Soát Internal Covariate Shift (Ioffe & Szegedy, 2015)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–08s (Câu hỏi thách thức) • Hình ảnh: Dòng chảy gradient rực lửa bùng nổ xé toạc các tầng mạng nơ-ron sâu, các con số rung lắc mất kiểm soát trong không gian tối. • Lời thoại: "Khi một mạng"*
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_21_batch_normalization.py SmoothingOptimizationLandscapeScene
  ```

#### `EP21_BatchNormVsLayerNormTensorScene` — BatchNormVsLayerNormTensorScene
- **Tập / Chủ đề**: Tập 21 — *TÔI LÀM VIỆC — SHORT TẬP 21: BATCH NORMALIZATION & CÂN BẰNG GRADIENT*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_21_batch_normalization.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_21_batch_normalization.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `6` | Thời lượng ước tính: `11.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Chuẩn Hóa Lô Batch Normalization & Kiểm Soát Internal Covariate Shift (Ioffe & Szegedy, 2015)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–08s (Câu hỏi thách thức) • Hình ảnh: Dòng chảy gradient rực lửa bùng nổ xé toạc các tầng mạng nơ-ron sâu, các con số rung lắc mất kiểm soát trong không gian tối. • Lời thoại: "Khi một mạng"*
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_21_batch_normalization.py BatchNormVsLayerNormTensorScene
  ```

#### `EP22_NonlinearFoldingSpaceScene` — NonlinearFoldingSpaceScene
- **Tập / Chủ đề**: Tập 22 — *TÔI LÀM VIỆC — TẬP 22: HÀM KÍCH HOẠT PHI TUYẾN & BIẾN HÌNH KHÔNG GIAN BIỂU DIỄN*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_22_nonlinear_activations.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_22_nonlinear_activations.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `4` | Thời lượng ước tính: `8.0s`
- **Căn cứ khoa học / Tiên đề toán học**: **Định Lý Xấp Xỉ Phổ Quát & Các Hàm Kích Hoạt Phi Tuyến (Cybenko 1989, Hornik 1991)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–32s (Ảo Ảnh Sụp Đổ Tuyến Tính & Định Lý Cybenko) • Hình ảnh: B-roll xưởng cơ khí chính xác đêm muộn, người kỹ sư tĩnh lặng trước màn hình terminal với ma trận tích, chuyển sang Manim mô ph"*
- **Công thức LaTeX cốt lõi**:
  - `$\prod_{i=1}^L W_i \cdot x = W_{\text{eff}} \cdot x$`
  - `$F(x) = \sum_{i=1}^N v_i \sigma(w_i^T x + b_i)$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_22_nonlinear_activations.py NonlinearFoldingSpaceScene
  ```

#### `EP22_ReLUvsGELUvsSwishScene` — ReLUvsGELUvsSwishScene
- **Tập / Chủ đề**: Tập 22 — *TÔI LÀM VIỆC — TẬP 22: HÀM KÍCH HOẠT PHI TUYẾN & BIẾN HÌNH KHÔNG GIAN BIỂU DIỄN*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_22_nonlinear_activations.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_22_nonlinear_activations.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `7` | Thời lượng ước tính: `12.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Định Lý Xấp Xỉ Phổ Quát & Các Hàm Kích Hoạt Phi Tuyến (Cybenko 1989, Hornik 1991)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–32s (Ảo Ảnh Sụp Đổ Tuyến Tính & Định Lý Cybenko) • Hình ảnh: B-roll xưởng cơ khí chính xác đêm muộn, người kỹ sư tĩnh lặng trước màn hình terminal với ma trận tích, chuyển sang Manim mô ph"*
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_22_nonlinear_activations.py ReLUvsGELUvsSwishScene
  ```

#### `EP22_UniversalApproximationFoldScene` — UniversalApproximationFoldScene
- **Tập / Chủ đề**: Tập 22 — *TÔI LÀM VIỆC — TẬP 22: HÀM KÍCH HOẠT PHI TUYẾN & BIẾN HÌNH KHÔNG GIAN BIỂU DIỄN*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_22_nonlinear_activations.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_22_nonlinear_activations.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `5` | Thời lượng ước tính: `9.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Định Lý Xấp Xỉ Phổ Quát & Các Hàm Kích Hoạt Phi Tuyến (Cybenko 1989, Hornik 1991)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–32s (Ảo Ảnh Sụp Đổ Tuyến Tính & Định Lý Cybenko) • Hình ảnh: B-roll xưởng cơ khí chính xác đêm muộn, người kỹ sư tĩnh lặng trước màn hình terminal với ma trận tích, chuyển sang Manim mô ph"*
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_22_nonlinear_activations.py UniversalApproximationFoldScene
  ```

#### `EP23_ConvolutionSlidingWindowKernelScene` — ConvolutionSlidingWindowKernelScene
- **Tập / Chủ đề**: Tập 23 — *TÔI LÀM VIỆC — TẬP 23: TÍCH CHẬP CONVOLUTION & PHÉP BIẾN ĐỔI FOURIER*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_23_convolution_fourier.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_23_convolution_fourier.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `6` | Thời lượng ước tính: `11.0s`
- **Căn cứ khoa học / Tiên đề toán học**: **Định Lý Tích Chập Fourier & Miền Tần Số Trong Xử Lý Tín Hiệu (Joseph Fourier 1822)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–32s (Ảo Ảnh Không Gian & Bản Chất Của Phép Tích Chập) • Hình ảnh: B-roll trạm cơ khí chính xác ban đêm, ống kính macro quét qua cấu trúc vi mạch bán dẫn, chuyển sang Manim mô phỏng ma trận"*
- **Công thức LaTeX cốt lõi**:
  - `$(I * K)(i, j) = \sum_{m, n} I(i-m, j-n) K(m, n)$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_23_convolution_fourier.py ConvolutionSlidingWindowKernelScene
  ```

#### `EP23_FourierConvolutionTheoremDualScene` — FourierConvolutionTheoremDualScene
- **Tập / Chủ đề**: Tập 23 — *TÔI LÀM VIỆC — TẬP 23: TÍCH CHẬP CONVOLUTION & PHÉP BIẾN ĐỔI FOURIER*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_23_convolution_fourier.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_23_convolution_fourier.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `5` | Thời lượng ước tính: `9.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Định Lý Tích Chập Fourier & Miền Tần Số Trong Xử Lý Tín Hiệu (Joseph Fourier 1822)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–32s (Ảo Ảnh Không Gian & Bản Chất Của Phép Tích Chập) • Hình ảnh: B-roll trạm cơ khí chính xác ban đêm, ống kính macro quét qua cấu trúc vi mạch bán dẫn, chuyển sang Manim mô phỏng ma trận"*
- **Công thức LaTeX cốt lõi**:
  - `$(f * g)(t) = \int_{-\infty}^\infty f(\tau) g(t - \tau) d\tau \quad \implies \quad \mathcal{O}(N^2)$`
  - `$\mathcal{F}\{f * g\} = \mathcal{F}\{f\} \cdot \mathcal{F}\{g\} \quad \implies \quad \mathcal{O}(N \log N)$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_23_convolution_fourier.py FourierConvolutionTheoremDualScene
  ```

#### `EP23_SpectralOperatorAndViTEvolutionScene` — SpectralOperatorAndViTEvolutionScene
- **Tập / Chủ đề**: Tập 23 — *TÔI LÀM VIỆC — TẬP 23: TÍCH CHẬP CONVOLUTION & PHÉP BIẾN ĐỔI FOURIER*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_23_convolution_fourier.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_23_convolution_fourier.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `5` | Thời lượng ước tính: `9.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Định Lý Tích Chập Fourier & Miền Tần Số Trong Xử Lý Tín Hiệu (Joseph Fourier 1822)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–32s (Ảo Ảnh Không Gian & Bản Chất Của Phép Tích Chập) • Hình ảnh: B-roll trạm cơ khí chính xác ban đêm, ống kính macro quét qua cấu trúc vi mạch bán dẫn, chuyển sang Manim mô phỏng ma trận"*
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_23_convolution_fourier.py SpectralOperatorAndViTEvolutionScene
  ```

#### `EP24_CausalHierarchyLadderScene` — CausalHierarchyLadderScene
- **Tập / Chủ đề**: Tập 24 — *TÔI LÀM VIỆC — TẬP 24: CAUSAL INFERENCE & CAN THIỆP DO-CALCULUS*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_24_causal_inference.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_24_causal_inference.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `5` | Thời lượng ước tính: `10.0s`
- **Căn cứ khoa học / Tiên đề toán học**: **Lý Thuyết Suy Luận Nhân Quả Causal Inference & Tiêu Chuẩn Cửa Sau Do-Calculus (Judea Pearl, 2000)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–35s (Nghịch Lý Tương Quan & Chiếc Bóng Của Thực Tại) • Hình ảnh: B-roll xưởng kỹ thuật đêm muộn tĩnh lặng, ánh sáng màn hình hắt lên khuôn mặt suy tư của người kỹ sư, chuyển sang Manim mô "*
- **Công thức LaTeX cốt lõi**:
  - `$P(Y_{X=x'} = y' \mid X=x, Y=y) \quad \text{--} \quad \text{What if we had acted differently?}$`
  - `$P(Y=y \mid do(X=x)) \quad \text{--} \quad \text{What will happen if we take action } X=x\text{?}$`
  - `$P(Y=y \mid X=x) \quad \text{--} \quad \text{What does seeing } X=x \text{ tell us about } Y\text{?}$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_24_causal_inference.py CausalHierarchyLadderScene
  ```

#### `EP24_BackdoorCriterionGraphSurgeryScene` — BackdoorCriterionGraphSurgeryScene
- **Tập / Chủ đề**: Tập 24 — *TÔI LÀM VIỆC — TẬP 24: CAUSAL INFERENCE & CAN THIỆP DO-CALCULUS*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_24_causal_inference.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_24_causal_inference.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `4` | Thời lượng ước tính: `8.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Lý Thuyết Suy Luận Nhân Quả Causal Inference & Tiêu Chuẩn Cửa Sau Do-Calculus (Judea Pearl, 2000)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–35s (Nghịch Lý Tương Quan & Chiếc Bóng Của Thực Tại) • Hình ảnh: B-roll xưởng kỹ thuật đêm muộn tĩnh lặng, ánh sáng màn hình hắt lên khuôn mặt suy tư của người kỹ sư, chuyển sang Manim mô "*
- **Công thức LaTeX cốt lõi**:
  - `$Z$`
  - `$X$`
  - `$Y$`
  - `$P(Y = y \mid do(X = x)) = \sum_{z} P(Y = y \mid X = x, Z = z) P(Z = z)$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_24_causal_inference.py BackdoorCriterionGraphSurgeryScene
  ```

#### `EP24_CounterfactualParallelWorldsScene` — CounterfactualParallelWorldsScene
- **Tập / Chủ đề**: Tập 24 — *TÔI LÀM VIỆC — TẬP 24: CAUSAL INFERENCE & CAN THIỆP DO-CALCULUS*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_24_causal_inference.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_24_causal_inference.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `4` | Thời lượng ước tính: `8.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Lý Thuyết Suy Luận Nhân Quả Causal Inference & Tiêu Chuẩn Cửa Sau Do-Calculus (Judea Pearl, 2000)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–35s (Nghịch Lý Tương Quan & Chiếc Bóng Của Thực Tại) • Hình ảnh: B-roll xưởng kỹ thuật đêm muộn tĩnh lặng, ánh sáng màn hình hắt lên khuôn mặt suy tư của người kỹ sư, chuyển sang Manim mô "*
- **Công thức LaTeX cốt lõi**:
  - `$P(Y_{X=x'} = y' \mid X=x, Y=y) = \sum_u P(Y(x') = y' \mid u) P(u \mid x, y)$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_24_causal_inference.py CounterfactualParallelWorldsScene
  ```

#### `EP103_MLAttentionMechanismScene` — MLAttentionMechanismScene
- **Tập / Chủ đề**: Tập 103 — *Manim Science — Deep Learning: Scaled Dot-Product Attention*
- **Tệp nguồn**: [`.agents/skills/manim-production/references/templates/template_ml.py`](file:////home/zen/hermes-agent/.agents/skills/manim-production/references/templates/template_ml.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `4` | Thời lượng ước tính: `8.0s`
- **Căn cứ khoa học / Tiên đề toán học**: **Cơ Chế Scaled Dot-Product Attention Ma Trận Softmax (Vaswani et al., 2017)**
- **Công thức LaTeX cốt lõi**:
  - `$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/.agents/skills/manim-production/references/templates/template_ml.py MLAttentionMechanismScene
  ```

### 📐 TOÁN HỌC & ĐẠI SỐ TUYẾN TÍNH (PURE MATH 3B1B)

#### `EP04_SimpsonScatterRegressionScene` — SimpsonScatterRegressionScene
- **Tập / Chủ đề**: Tập 04 — *TẬP 04: NGHỊCH LÝ SIMPSON — KHI DỮ LIỆU NÓI THẬT, NHƯNG KẾT LUẬN LẠI SAI*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_04_simpson_paradox.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_04_simpson_paradox.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `5` | Thời lượng ước tính: `11.0s`
- **Căn cứ khoa học / Tiên đề toán học**: **Nghịch Lý Simpson & Hiện Tượng Đảo Chiều Thống Kê Dữ Liệu (Edward H. Simpson, 1951)**
- **Kịch bản & Ngữ cảnh**: *"Scene 4: Simpson's Paradox in 2D Scatter Plot & Regression Reversal
Within each group: Slope > 0 (Positive correlation)
Combined across groups: Slope < 0 (Negative correlation)"*
- **Công thức LaTeX cốt lõi**:
  - `$\beta_A > 0 \text{ (+)}$`
  - `$\beta_B > 0 \text{ (+)}$`
  - `$\beta_{\text{total}} < 0 \text{ (-)}$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_04_simpson_paradox.py SimpsonScatterRegressionScene
  ```

#### `EP04_ConfoundingVariable3DScene` — ConfoundingVariable3DScene
- **Tập / Chủ đề**: Tập 04 — *TẬP 04: NGHỊCH LÝ SIMPSON — KHI DỮ LIỆU NÓI THẬT, NHƯNG KẾT LUẬN LẠI SAI*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_04_simpson_paradox.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_04_simpson_paradox.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `2` | Thời lượng ước tính: `8.0s`
- **Căn cứ khoa học / Tiên đề toán học**: **Nghịch Lý Simpson & Hiện Tượng Đảo Chiều Thống Kê Dữ Liệu (Edward H. Simpson, 1951)**
- **Kịch bản & Ngữ cảnh**: *"Scene 5: 3D Dimension Rotation revealing the Confounding Variable (z-axis)"*
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_04_simpson_paradox.py ConfoundingVariable3DScene
  ```

#### `EP06_GaltonBoardScene` — GaltonBoardScene
- **Tập / Chủ đề**: Tập 06 — *TẬP 06 SHORTS: TẠI SAO MỌI HỖN LOẠN ĐỀU QUY VỀ ĐƯỜNG CONG GAUSS?*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_06_clt_gaussian.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_06_clt_gaussian.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `7` | Thời lượng ước tính: `12.0s`
- **Căn cứ khoa học / Tiên đề toán học**: **Định Lý Giới Hạn Trung Tâm CLT & Phân Phối Chuẩn Gaussian (Laplace 1810, Lyapunov 1901)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–07.5s (The Paradox Hook) • Hình ảnh: Một hạt bi kim loại nảy loạn xạ qua bàn đinh Quincunx, rơi vào một ô bất kỳ dưới đáy hộp hoàn toàn ngẫu nhiên. • Lời thoại: "Một hạt bi rơi qua mê cung"*
- **Công thức LaTeX cốt lõi**:
  - `$f(x) = \frac{1}{\sigma \sqrt{2\pi}} e^{-\frac{(x-\mu)^2}{2\sigma^2}}$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_06_clt_gaussian.py GaltonBoardScene
  ```

#### `EP06_CLTConvergenceScene` — CLTConvergenceScene
- **Tập / Chủ đề**: Tập 06 — *TẬP 06 SHORTS: TẠI SAO MỌI HỖN LOẠN ĐỀU QUY VỀ ĐƯỜNG CONG GAUSS?*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_06_clt_gaussian.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_06_clt_gaussian.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `5` | Thời lượng ước tính: `11.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Định Lý Giới Hạn Trung Tâm CLT & Phân Phối Chuẩn Gaussian (Laplace 1810, Lyapunov 1901)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–07.5s (The Paradox Hook) • Hình ảnh: Một hạt bi kim loại nảy loạn xạ qua bàn đinh Quincunx, rơi vào một ô bất kỳ dưới đáy hộp hoàn toàn ngẫu nhiên. • Lời thoại: "Một hạt bi rơi qua mê cung"*
- **Công thức LaTeX cốt lõi**:
  - `$Z = \frac{\bar{X}_n - \mu}{\sigma / \sqrt{n}} \xrightarrow{d} \mathcal{N}(0, 1)$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_06_clt_gaussian.py CLTConvergenceScene
  ```

#### `EP06_GaussianWeightInitScene` — GaussianWeightInitScene
- **Tập / Chủ đề**: Tập 06 — *TẬP 06 SHORTS: TẠI SAO MỌI HỖN LOẠN ĐỀU QUY VỀ ĐƯỜNG CONG GAUSS?*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_06_clt_gaussian.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_06_clt_gaussian.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `4` | Thời lượng ước tính: `8.0s`
- **Căn cứ khoa học / Tiên đề toán học**: **Định Lý Giới Hạn Trung Tâm CLT & Phân Phối Chuẩn Gaussian (Laplace 1810, Lyapunov 1901)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–07.5s (The Paradox Hook) • Hình ảnh: Một hạt bi kim loại nảy loạn xạ qua bàn đinh Quincunx, rơi vào một ô bất kỳ dưới đáy hộp hoàn toàn ngẫu nhiên. • Lời thoại: "Một hạt bi rơi qua mê cung"*
- **Công thức LaTeX cốt lõi**:
  - `$W_{ij} \sim \mathcal{N}\left(0, \sqrt{\frac{2}{n_{in}}}\right) \quad \implies \quad \operatorname{Var}(a^{[L]}) = \operatorname{Var}(a^{[0]})$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_06_clt_gaussian.py GaussianWeightInitScene
  ```

#### `EP06_DiffusionNoiseDenoiseScene` — DiffusionNoiseDenoiseScene
- **Tập / Chủ đề**: Tập 06 — *TẬP 06 SHORTS: TẠI SAO MỌI HỖN LOẠN ĐỀU QUY VỀ ĐƯỜNG CONG GAUSS?*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_06_clt_gaussian.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_06_clt_gaussian.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `5` | Thời lượng ước tính: `9.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Định Lý Giới Hạn Trung Tâm CLT & Phân Phối Chuẩn Gaussian (Laplace 1810, Lyapunov 1901)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–07.5s (The Paradox Hook) • Hình ảnh: Một hạt bi kim loại nảy loạn xạ qua bàn đinh Quincunx, rơi vào một ô bất kỳ dưới đáy hộp hoàn toàn ngẫu nhiên. • Lời thoại: "Một hạt bi rơi qua mê cung"*
- **Công thức LaTeX cốt lõi**:
  - `$x_{t-1} = \frac{1}{\sqrt{\alpha_t}} \left( x_t - \frac{1 - \alpha_t}{\sqrt{1 - \bar{\alpha}_t}} \boldsymbol{\epsilon}_\theta(x_t, t) \right) + \sigma_t \mathbf{z}$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_06_clt_gaussian.py DiffusionNoiseDenoiseScene
  ```

#### `EP10_CovarianceMatrixEllipseScene` — CovarianceMatrixEllipseScene
- **Tập / Chủ đề**: Tập 10 — *TÔI LÀM VIỆC — TẬP 10: NGHỆ THUẬT NÉN TRI THỨC (MA TRẬN HIỆP PHƯƠNG SAI & GIẢM CHIỀU PCA)*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_10_pca_covariance.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_10_pca_covariance.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `4` | Thời lượng ước tính: `8.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Phân Tích Thành Phần Chính PCA & Ma Trận Hiệp Phương Sai (Karl Pearson 1901, Hotelling 1933)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–20s (Lời nguyền số chiều và gánh nặng của cỗ máy) • Hình ảnh: Màn hình hiển thị ma trận dữ liệu khổng lồ với hàng nghìn cột, các chiều không gian chồng chéo dày đặc gây tắc nghẽn tính toán"*
- **Công thức LaTeX cốt lõi**:
  - `$\Sigma = \begin{bmatrix} \text{Var}(X) & \text{Cov}(X,Y) \\ \text{Cov}(Y,X) & \text{Var}(Y) \end{bmatrix}$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_10_pca_covariance.py CovarianceMatrixEllipseScene
  ```

#### `EP10_EigenvectorMaxVarianceScene` — EigenvectorMaxVarianceScene
- **Tập / Chủ đề**: Tập 10 — *TÔI LÀM VIỆC — TẬP 10: NGHỆ THUẬT NÉN TRI THỨC (MA TRẬN HIỆP PHƯƠNG SAI & GIẢM CHIỀU PCA)*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_10_pca_covariance.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_10_pca_covariance.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `5` | Thời lượng ước tính: `10.0s`
- **Căn cứ khoa học / Tiên đề toán học**: **Phân Tích Thành Phần Chính PCA & Ma Trận Hiệp Phương Sai (Karl Pearson 1901, Hotelling 1933)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–20s (Lời nguyền số chiều và gánh nặng của cỗ máy) • Hình ảnh: Màn hình hiển thị ma trận dữ liệu khổng lồ với hàng nghìn cột, các chiều không gian chồng chéo dày đặc gây tắc nghẽn tính toán"*
- **Công thức LaTeX cốt lõi**:
  - `$\vec{v}_1 \ (\lambda_1 \text{ Max})$`
  - `$\vec{v}_2 \ (\lambda_2 \approx 0)$`
  - `$\Sigma \vec{v} = \lambda \vec{v}$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_10_pca_covariance.py EigenvectorMaxVarianceScene
  ```

#### `EP10_PCAOrthogonalProjectionScene` — PCAOrthogonalProjectionScene
- **Tập / Chủ đề**: Tập 10 — *TÔI LÀM VIỆC — TẬP 10: NGHỆ THUẬT NÉN TRI THỨC (MA TRẬN HIỆP PHƯƠNG SAI & GIẢM CHIỀU PCA)*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_10_pca_covariance.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_10_pca_covariance.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `6` | Thời lượng ước tính: `11.2s`
- **Căn cứ khoa học / Tiên đề toán học**: **Phân Tích Thành Phần Chính PCA & Ma Trận Hiệp Phương Sai (Karl Pearson 1901, Hotelling 1933)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–20s (Lời nguyền số chiều và gánh nặng của cỗ máy) • Hình ảnh: Màn hình hiển thị ma trận dữ liệu khổng lồ với hàng nghìn cột, các chiều không gian chồng chéo dày đặc gây tắc nghẽn tính toán"*
- **Công thức LaTeX cốt lõi**:
  - `$\vec{v}_1 \ (\text{PC 1 Axis})$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_10_pca_covariance.py PCAOrthogonalProjectionScene
  ```

#### `EP10_LatentSpaceCompressionScene` — LatentSpaceCompressionScene
- **Tập / Chủ đề**: Tập 10 — *TÔI LÀM VIỆC — TẬP 10: NGHỆ THUẬT NÉN TRI THỨC (MA TRẬN HIỆP PHƯƠNG SAI & GIẢM CHIỀU PCA)*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_10_pca_covariance.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_10_pca_covariance.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `5` | Thời lượng ước tính: `10.0s`
- **Căn cứ khoa học / Tiên đề toán học**: **Phân Tích Thành Phần Chính PCA & Ma Trận Hiệp Phương Sai (Karl Pearson 1901, Hotelling 1933)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–20s (Lời nguyền số chiều và gánh nặng của cỗ máy) • Hình ảnh: Màn hình hiển thị ma trận dữ liệu khổng lồ với hàng nghìn cột, các chiều không gian chồng chéo dày đặc gây tắc nghẽn tính toán"*
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_10_pca_covariance.py LatentSpaceCompressionScene
  ```

#### `EP15_BayesTheoremEquationScene` — BayesTheoremEquationScene
- **Tập / Chủ đề**: Tập 15 — *TÔI LÀM VIỆC — TẬP 15: ĐỊNH LÝ BAYES & BẢN CHẤT CỦA SỰ THAY ĐỔI NIỀM TIN*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_15_bayesian_inference.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_15_bayesian_inference.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `4` | Thời lượng ước tính: `9.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Quy Tắc Cập Nhật Suy Luận Bayes Liên Tục & Phân Phối Beta-Binomial**
- **Kịch bản & Ngữ cảnh**: *"Scene 2: Core structure of Bayes Theorem: Prior, Likelihood, Posterior."*
- **Công thức LaTeX cốt lõi**:
  - `$P(H \mid D) = \frac{P(D \mid H) \cdot P(H)}{P(D)}$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_15_bayesian_inference.py BayesTheoremEquationScene
  ```

#### `EP15_BayesianBeliefUpdateLoopScene` — BayesianBeliefUpdateLoopScene
- **Tập / Chủ đề**: Tập 15 — *TÔI LÀM VIỆC — TẬP 15: ĐỊNH LÝ BAYES & BẢN CHẤT CỦA SỰ THAY ĐỔI NIỀM TIN*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_15_bayesian_inference.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_15_bayesian_inference.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `5` | Thời lượng ước tính: `11.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Quy Tắc Cập Nhật Suy Luận Bayes Liên Tục & Phân Phối Beta-Binomial**
- **Kịch bản & Ngữ cảnh**: *"Scene 3: Iterative Bayesian updating: Prior narrows and converges as data arrives."*
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_15_bayesian_inference.py BayesianBeliefUpdateLoopScene
  ```

#### `EP15_MAPWeightDecayConnectionScene` — MAPWeightDecayConnectionScene
- **Tập / Chủ đề**: Tập 15 — *TÔI LÀM VIỆC — TẬP 15: ĐỊNH LÝ BAYES & BẢN CHẤT CỦA SỰ THAY ĐỔI NIỀM TIN*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_15_bayesian_inference.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_15_bayesian_inference.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `4` | Thời lượng ước tính: `9.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Quy Tắc Cập Nhật Suy Luận Bayes Liên Tục & Phân Phối Beta-Binomial**
- **Kịch bản & Ngữ cảnh**: *"Scene 4: Maximum A Posteriori (MAP) and its exact equivalence to L2 Regularization."*
- **Công thức LaTeX cốt lõi**:
  - `$\arg\max_{\theta} \log P(\theta \mid D) = \arg\max_{\theta} \left[ \log P(D \mid \theta) + \log P(\theta) \right]$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_15_bayesian_inference.py MAPWeightDecayConnectionScene
  ```

#### `EP15_BaseRateFallacyScene` — BaseRateFallacyScene
- **Tập / Chủ đề**: Tập 15 — *TÔI LÀM VIỆC — TẬP 15: ĐỊNH LÝ BAYES & BẢN CHẤT CỦA SỰ THAY ĐỔI NIỀM TIN*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_15_bayesian_inference.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_15_bayesian_inference.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `4` | Thời lượng ước tính: `9.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Quy Tắc Cập Nhật Suy Luận Bayes Liên Tục & Phân Phối Beta-Binomial**
- **Kịch bản & Ngữ cảnh**: *"Scene 5: Base Rate Fallacy: Why a 99% accurate test yields < 1% posterior."*
- **Công thức LaTeX cốt lõi**:
  - `$P(\text{Sick} \mid \text{Positive}) = \frac{1}{1 + 100} \approx 0.99\%$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_15_bayesian_inference.py BaseRateFallacyScene
  ```

#### `EP16_SVDGeometricDecompositionScene` — SVDGeometricDecompositionScene
- **Tập / Chủ đề**: Tập 16 — *TÔI LÀM VIỆC — TẬP 16: PHÉP PHÂN RÃ SVD & TRỤC XƯƠNG SỐNG NÉN VẠN CHIỀU*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_16_svd_matrix_decomposition.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_16_svd_matrix_decomposition.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `6` | Thời lượng ước tính: `13.0s`
- **Căn cứ khoa học / Tiên đề toán học**: **Phân Rã Giá Trị Kỳ Dị SVD & Nén Ma Trận Hạng Thấp (Eckart-Young-Mirsky Theorem, 1936)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–30s (Sự Cồng Kềnh Của Không Gian Vạn Chiều) • Hình ảnh: B-roll bàn làm việc đêm tối, màn hình hiện ma trận khổng lồ hàng triệu hàng và cột, sau đó chuyển sang Manim biểu diễn một lưới tọa "*
- **Công thức LaTeX cốt lõi**:
  - `$A = U \cdot \Sigma \cdot V^T$`
  - `$\sigma_1$`
  - `$\sigma_2$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_16_svd_matrix_decomposition.py SVDGeometricDecompositionScene
  ```

#### `EP16_LowRankApproximationScene` — LowRankApproximationScene
- **Tập / Chủ đề**: Tập 16 — *TÔI LÀM VIỆC — TẬP 16: PHÉP PHÂN RÃ SVD & TRỤC XƯƠNG SỐNG NÉN VẠN CHIỀU*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_16_svd_matrix_decomposition.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_16_svd_matrix_decomposition.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `4` | Thời lượng ước tính: `8.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Phân Rã Giá Trị Kỳ Dị SVD & Nén Ma Trận Hạng Thấp (Eckart-Young-Mirsky Theorem, 1936)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–30s (Sự Cồng Kềnh Của Không Gian Vạn Chiều) • Hình ảnh: B-roll bàn làm việc đêm tối, màn hình hiện ma trận khổng lồ hàng triệu hàng và cột, sau đó chuyển sang Manim biểu diễn một lưới tọa "*
- **Công thức LaTeX cốt lõi**:
  - `$A_k = \sum_{i=1}^{k} \sigma_i u_i v_i^T$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_16_svd_matrix_decomposition.py LowRankApproximationScene
  ```

#### `EP16_LoRAMatrixDecompositionScene` — LoRAMatrixDecompositionScene
- **Tập / Chủ đề**: Tập 16 — *TÔI LÀM VIỆC — TẬP 16: PHÉP PHÂN RÃ SVD & TRỤC XƯƠNG SỐNG NÉN VẠN CHIỀU*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_16_svd_matrix_decomposition.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_16_svd_matrix_decomposition.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `3` | Thời lượng ước tính: `7.0s`
- **Căn cứ khoa học / Tiên đề toán học**: **Phân Rã Giá Trị Kỳ Dị SVD & Nén Ma Trận Hạng Thấp (Eckart-Young-Mirsky Theorem, 1936)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–30s (Sự Cồng Kềnh Của Không Gian Vạn Chiều) • Hình ảnh: B-roll bàn làm việc đêm tối, màn hình hiện ma trận khổng lồ hàng triệu hàng và cột, sau đó chuyển sang Manim biểu diễn một lưới tọa "*
- **Công thức LaTeX cốt lõi**:
  - `$W_0 \in \mathbb{R}^{d \times d}$`
  - `$+$`
  - `$B$`
  - `$d \times r$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_16_svd_matrix_decomposition.py LoRAMatrixDecompositionScene
  ```

#### `EP18_MonteCarloPiEstimationScene` — MonteCarloPiEstimationScene
- **Tập / Chủ đề**: Tập 18 — *TÔI LÀM VIỆC — SHORT TẬP 18: PHƯƠNG PHÁP MONTE CARLO & THUẬT TOÁN MCMC*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_18_monte_carlo_mcmc.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_18_monte_carlo_mcmc.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `3` | Thời lượng ước tính: `6.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Phương Pháp Lấy Mẫu Monte Carlo & Chuỗi Markov MCMC (Metropolis-Hastings 1953, Ulam)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–08s (Câu hỏi thách thức) • Hình ảnh: Hàng ngàn hạt ánh sáng ngẫu nhiên rơi xuống màn hình tối, hội tụ thành hình tròn số Pi 3.14159 và bàn cờ AlphaGo. • Lời thoại: "Nếu một phương trình to"*
- **Công thức LaTeX cốt lõi**:
  - `$\pi \approx 4 \times \frac{N_{\text{inside}}}{N_{\text{total}}}$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_18_monte_carlo_mcmc.py MonteCarloPiEstimationScene
  ```

#### `EP18_MCMCRandomWalkLandscapeScene` — MCMCRandomWalkLandscapeScene
- **Tập / Chủ đề**: Tập 18 — *TÔI LÀM VIỆC — SHORT TẬP 18: PHƯƠNG PHÁP MONTE CARLO & THUẬT TOÁN MCMC*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_18_monte_carlo_mcmc.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_18_monte_carlo_mcmc.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `6` | Thời lượng ước tính: `11.0s`
- **Căn cứ khoa học / Tiên đề toán học**: **Phương Pháp Lấy Mẫu Monte Carlo & Chuỗi Markov MCMC (Metropolis-Hastings 1953, Ulam)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–08s (Câu hỏi thách thức) • Hình ảnh: Hàng ngàn hạt ánh sáng ngẫu nhiên rơi xuống màn hình tối, hội tụ thành hình tròn số Pi 3.14159 và bàn cờ AlphaGo. • Lời thoại: "Nếu một phương trình to"*
- **Công thức LaTeX cốt lõi**:
  - `$p(x) = \frac{p^*(x)}{Z}$`
  - `$\alpha = \min\left(1, \frac{p^*(x')}{p^*(x)}\right)$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_18_monte_carlo_mcmc.py MCMCRandomWalkLandscapeScene
  ```

#### `EP18_MonteCarloTreeSearchScene` — MonteCarloTreeSearchScene
- **Tập / Chủ đề**: Tập 18 — *TÔI LÀM VIỆC — SHORT TẬP 18: PHƯƠNG PHÁP MONTE CARLO & THUẬT TOÁN MCMC*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_18_monte_carlo_mcmc.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_18_monte_carlo_mcmc.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `4` | Thời lượng ước tính: `8.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Phương Pháp Lấy Mẫu Monte Carlo & Chuỗi Markov MCMC (Metropolis-Hastings 1953, Ulam)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–08s (Câu hỏi thách thức) • Hình ảnh: Hàng ngàn hạt ánh sáng ngẫu nhiên rơi xuống màn hình tối, hội tụ thành hình tròn số Pi 3.14159 và bàn cờ AlphaGo. • Lời thoại: "Nếu một phương trình to"*
- **Công thức LaTeX cốt lõi**:
  - `$\text{Score} = \frac{W_i}{N_i} + c \sqrt{\frac{\ln N_p}{N_i}}$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_18_monte_carlo_mcmc.py MonteCarloTreeSearchScene
  ```

#### `EP20_HessianMatrixCurvatureScene` — HessianMatrixCurvatureScene
- **Tập / Chủ đề**: Tập 20 — *TÔI LÀM VIỆC — TẬP 20: MA TRẬN HESSIAN & ĐIỂM YÊN NGỰA SADDLE POINTS*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_20_hessian_saddle_points.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_20_hessian_saddle_points.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `5` | Thời lượng ước tính: `9.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Ma Trận Hessian, Điểm Yên Ngựa Saddle Points & Độ Cong Vi Phân**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–30s (Vực Sâu Tối Ưu Phi Lồi & Ảo Ảnh Đạo Hàm Bằng Không) • Hình ảnh: B-roll xưởng tiện đêm muộn, mũi dao gọt kim loại trên mặt cong cơ khí phản chiếu ánh đèn vàng, chuyển sang Manim bề mặt"*
- **Công thức LaTeX cốt lõi**:
  - `$H = \begin{bmatrix} \frac{\partial^2 f}{\partial x_1^2} & \frac{\partial^2 f}{\partial x_1 \partial x_2} \\ \frac{\partial^2 f}{\partial x_2 \partial x_1} & \frac{\partial^2 f}{\partial x_2^2} \end{bmatrix}$`
  - `$H v_i = \lambda_i v_i$`
  - `$\lambda_i > 0, \forall i$`
  - `$\lambda_i < 0, \forall i$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_20_hessian_saddle_points.py HessianMatrixCurvatureScene
  ```

#### `EP20_DauphinExponentialSaddleScene` — DauphinExponentialSaddleScene
- **Tập / Chủ đề**: Tập 20 — *TÔI LÀM VIỆC — TẬP 20: MA TRẬN HESSIAN & ĐIỂM YÊN NGỰA SADDLE POINTS*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_20_hessian_saddle_points.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_20_hessian_saddle_points.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `3` | Thời lượng ước tính: `6.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Ma Trận Hessian, Điểm Yên Ngựa Saddle Points & Độ Cong Vi Phân**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–30s (Vực Sâu Tối Ưu Phi Lồi & Ảo Ảnh Đạo Hàm Bằng Không) • Hình ảnh: B-roll xưởng tiện đêm muộn, mũi dao gọt kim loại trên mặt cong cơ khí phản chiếu ánh đèn vàng, chuyển sang Manim bề mặt"*
- **Công thức LaTeX cốt lõi**:
  - `$P(\text{Local Min}) \propto 2^{-N}$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_20_hessian_saddle_points.py DauphinExponentialSaddleScene
  ```

#### `EP20_EscapingSaddleMomentumScene` — EscapingSaddleMomentumScene
- **Tập / Chủ đề**: Tập 20 — *TÔI LÀM VIỆC — TẬP 20: MA TRẬN HESSIAN & ĐIỂM YÊN NGỰA SADDLE POINTS*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_20_hessian_saddle_points.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_20_hessian_saddle_points.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `6` | Thời lượng ước tính: `11.0s`
- **Căn cứ khoa học / Tiên đề toán học**: **Ma Trận Hessian, Điểm Yên Ngựa Saddle Points & Độ Cong Vi Phân**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–30s (Vực Sâu Tối Ưu Phi Lồi & Ảo Ảnh Đạo Hàm Bằng Không) • Hình ảnh: B-roll xưởng tiện đêm muộn, mũi dao gọt kim loại trên mặt cong cơ khí phản chiếu ánh đèn vàng, chuyển sang Manim bề mặt"*
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_20_hessian_saddle_points.py EscapingSaddleMomentumScene
  ```

#### `EP25_GrandMathematicalTimelineScene` — GrandMathematicalTimelineScene
- **Tập / Chủ đề**: Tập 25 — *TÔI LÀM VIỆC — TẬP 25: SHORT 30S*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_25_grand_mathematical_synthesis.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_25_grand_mathematical_synthesis.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `4` | Thời lượng ước tính: `8.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Đại Hợp Âm Toán Học AI & Triết Lý Đạo Làm Nghề Kỹ Thuật (ZenPham Synthesis, 2026)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–09s (Hook — Ảo Ảnh Của Những Lời Hứa Hẹn Hào Nhoáng) • Hình ảnh: B-roll người kỹ sư tĩnh lặng trước terminal đêm khuya, dòng chữ nổi bật: AI không phải là ma thuật. • Lời thoại: "Đừng để n"*
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_25_grand_mathematical_synthesis.py GrandMathematicalTimelineScene
  ```

#### `EP25_UnifiedMathematicalCoreMatrixScene` — UnifiedMathematicalCoreMatrixScene
- **Tập / Chủ đề**: Tập 25 — *TÔI LÀM VIỆC — TẬP 25: SHORT 30S*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_25_grand_mathematical_synthesis.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_25_grand_mathematical_synthesis.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `3` | Thời lượng ước tính: `7.0s`
- **Căn cứ khoa học / Tiên đề toán học**: **Đại Hợp Âm Toán Học AI & Triết Lý Đạo Làm Nghề Kỹ Thuật (ZenPham Synthesis, 2026)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–09s (Hook — Ảo Ảnh Của Những Lời Hứa Hẹn Hào Nhoáng) • Hình ảnh: B-roll người kỹ sư tĩnh lặng trước terminal đêm khuya, dòng chữ nổi bật: AI không phải là ma thuật. • Lời thoại: "Đừng để n"*
- **Công thức LaTeX cốt lõi**:
  - `$y = W x + b \quad \cdot \quad A = U \Sigma V^T$`
  - `$w \leftarrow w - \eta \nabla L(w) \quad \cdot \quad H = \nabla^2 L$`
  - `$H(P, Q) = -\sum P(x) \log Q(x)$`
  - `$P(Y \mid do(X)) = \sum_z P(Y \mid X, z) P(z)$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_25_grand_mathematical_synthesis.py UnifiedMathematicalCoreMatrixScene
  ```

#### `EP25_TheCraftsmanWayFinalSynthesisScene` — TheCraftsmanWayFinalSynthesisScene
- **Tập / Chủ đề**: Tập 25 — *TÔI LÀM VIỆC — TẬP 25: SHORT 30S*
- **Tệp nguồn**: [`assets/scripts_video/manim_tap_25_grand_mathematical_synthesis.py`](file:////home/zen/hermes-agent/assets/scripts_video/manim_tap_25_grand_mathematical_synthesis.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `6` | Thời lượng ước tính: `12.0s`
- **Căn cứ khoa học / Tiên đề toán học**: **Đại Hợp Âm Toán Học AI & Triết Lý Đạo Làm Nghề Kỹ Thuật (ZenPham Synthesis, 2026)**
- **Kịch bản & Ngữ cảnh**: *"Đoạn 1: 00s–09s (Hook — Ảo Ảnh Của Những Lời Hứa Hẹn Hào Nhoáng) • Hình ảnh: B-roll người kỹ sư tĩnh lặng trước terminal đêm khuya, dòng chữ nổi bật: AI không phải là ma thuật. • Lời thoại: "Đừng để n"*
- **Công thức LaTeX cốt lõi**:
  - `$\text{Intelligence} = \lim_{t \to \infty} \left( \text{Mathematics} + \text{Humility} + \text{Craftsmanship} \right)$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/assets/scripts_video/manim_tap_25_grand_mathematical_synthesis.py TheCraftsmanWayFinalSynthesisScene
  ```

#### `EP105_Math3B1BMatrixScene` — Math3B1BMatrixScene
- **Tập / Chủ đề**: Tập 105 — *Manim Science — Toán Cao Cấp: Biến Đổi Ma Trận & Định Thức det(A)*
- **Tệp nguồn**: [`.agents/skills/manim-production/references/templates/template_math_3b1b.py`](file:////home/zen/hermes-agent/.agents/skills/manim-production/references/templates/template_math_3b1b.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `6` | Thời lượng ước tính: `11.0s`
- **Căn cứ khoa học / Tiên đề toán học**: **Biến Đổi Ma Trận Tuyến Tính & Ý Nghĩa Hình Học Định Thức det(A) (3Blue1Brown Standard)**
- **Công thức LaTeX cốt lõi**:
  - `$A = \begin{bmatrix} 1 & 1 \\ 0 & 1.5 \end{bmatrix}, \quad \det(A) = 1.5$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/.agents/skills/manim-production/references/templates/template_math_3b1b.py Math3B1BMatrixScene
  ```

### ⚡ VẬT LÝ & CƠ HỌC MÔ PHỎNG (PHYSICS)

#### `EP101_PhysicsPendulumScene` — PhysicsPendulumScene
- **Tập / Chủ đề**: Tập 101 — *Manim Science — Vật Lý: Dao Động Con Lắc Điều Hòa & Lực Lorentz*
- **Tệp nguồn**: [`.agents/skills/manim-production/references/templates/template_physics.py`](file:////home/zen/hermes-agent/.agents/skills/manim-production/references/templates/template_physics.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `5` | Thời lượng ước tính: `8.5s`
- **Căn cứ khoa học / Tiên đề toán học**: **Phương Trình Vi Phân Dao Động Điều Hòa & Bảo Toàn Cơ Năng (Newton, Euler)**
- **Công thức LaTeX cốt lõi**:
  - `$\frac{d^2\theta}{dt^2} + \frac{g}{L}\sin\theta = 0$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/.agents/skills/manim-production/references/templates/template_physics.py PhysicsPendulumScene
  ```

### 🧪 HÓA HỌC & CẤU TRÚC PHÂN TỬ (CHEMISTRY)

#### `EP102_ChemistryWaterMoleculeScene` — ChemistryWaterMoleculeScene
- **Tập / Chủ đề**: Tập 102 — *Manim Science — Hóa Học: Phân Tử Nước H2O & Lai Hóa sp3*
- **Tệp nguồn**: [`.agents/skills/manim-production/references/templates/template_chemistry.py`](file:////home/zen/hermes-agent/.agents/skills/manim-production/references/templates/template_chemistry.py)
- **Tính chất**: `🟢 DYNAMIC ANIMATION (Chuyển Động)` | Animations: `6` | Thời lượng ước tính: `11.0s`
- **Căn cứ khoa học / Tiên đề toán học**: **Cấu Trúc Không Gian Phân Tử, Mô Hình Lai Hóa sp3 & Moment Lưỡng Cực (Linus Pauling 1931)**
- **Công thức LaTeX cốt lõi**:
  - `$2\text{H}_2 + \text{O}_2 \xrightarrow{t^\circ} 2\text{H}_2\text{O}$`
- **Lệnh Render Docker 1 dòng**:
  ```bash
  docker run --rm -v "$PWD:/manim" manimcommunity/manim:latest manim -s -r 1920,1080 /manim/.agents/skills/manim-production/references/templates/template_chemistry.py ChemistryWaterMoleculeScene
  ```
