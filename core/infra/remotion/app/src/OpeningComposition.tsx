import React from "react";
import {
	AbsoluteFill,
	Easing,
	interpolate,
	spring,
	useCurrentFrame,
	useVideoConfig,
} from "remotion";

export type OpeningCompositionProps = {
	bookTitle: string;
	focusWords: string[];
	ipName: string;
	lineAppearTimes: number[];
	quoteLines: string[];
};

const BG = "#121920";
const TEXT = "#f3eee4";
const MUTED = "rgba(236,231,222,0.78)";
const ACCENT = "#e7c992";
const SERIF = '"Noto Serif SC", "Songti SC", "STSong", "SimSun", serif';
const SANS = '"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif';

const highlightLine = (line: string, focusWords: string[]) => {
	if (focusWords.length === 0) {
		return [{text: line, focused: false}];
	}

	const escaped = focusWords
		.filter(Boolean)
		.map((word) => word.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));

	if (escaped.length === 0) {
		return [{text: line, focused: false}];
	}

	const regex = new RegExp(`(${escaped.join("|")})`, "g");
	return line.split(regex).filter(Boolean).map((part) => ({
		text: part,
		focused: focusWords.includes(part),
	}));
};

export const OpeningComposition: React.FC<OpeningCompositionProps> = ({
	bookTitle,
	focusWords,
	ipName,
	lineAppearTimes,
	quoteLines,
}) => {
	const frame = useCurrentFrame();
	const {fps, height, width, durationInFrames} = useVideoConfig();
	const lineCount = Math.max(quoteLines.length, 1);
	const longestLine = quoteLines.reduce((max, line) => Math.max(max, line.length), 0);

	const backgroundScale = interpolate(frame, [0, 4 * fps], [1.03, 1], {
		easing: Easing.out(Easing.cubic),
		extrapolateRight: "clamp",
	});
	const backgroundShift = interpolate(frame, [0, 4 * fps], [14, -6], {
		easing: Easing.inOut(Easing.ease),
		extrapolateRight: "clamp",
	});

	const maxByHeight = Math.round(height * 0.152);
	const maxByWidth = longestLine > 0
		? Math.round((width * 0.94) / Math.max(longestLine, 1))
		: maxByHeight;
	const quoteFontSize = Math.max(88, Math.min(maxByHeight, maxByWidth, 122));
	const lineGap = Math.max(18, Math.round(quoteFontSize * 0.18));
	const bookFontSize = Math.max(44, Math.round(quoteFontSize * 0.44));
	const ipFontSize = Math.max(44, Math.round(quoteFontSize * 0.42)); // 再次大幅增大 IP 字号，基本接近书名字号
	const quoteOffsetY = lineCount >= 4 ? -0.6 : lineCount >= 3 ? -0.56 : -0.53;
	const mastheadDraw = interpolate(frame, [0.08 * fps, 0.72 * fps], [0, 1], {
		extrapolateLeft: "clamp",
		extrapolateRight: "clamp",
		easing: Easing.out(Easing.cubic),
	});
	const mastheadGlow = interpolate(frame, [0.08 * fps, 0.72 * fps, 1.5 * fps], [0.15, 1, 0.55], {
		extrapolateLeft: "clamp",
		extrapolateRight: "clamp",
	});
	const focusPulse = interpolate(frame, [1.05 * fps, 1.65 * fps, 2.6 * fps, 3.4 * fps], [0, 0.6, 0.22, 0], {
		extrapolateLeft: "clamp",
		extrapolateRight: "clamp",
	});

	// Camera slow zoom on the text
	const cameraZoom = interpolate(frame, [0, durationInFrames], [1, 1.06], {
		extrapolateRight: "clamp",
	});

	return (
		<AbsoluteFill style={{backgroundColor: BG, fontFamily: SANS}}>
			<AbsoluteFill
				style={{
					background:
						"radial-gradient(circle at 50% 22%, rgba(225, 201, 164, 0.12), transparent 24%), linear-gradient(180deg, rgba(6,10,14,0.18), rgba(6,10,14,0.5)), linear-gradient(135deg, #101820 0%, #26343d 52%, #131b22 100%)",
					transform: `scale(${backgroundScale}) translateX(${backgroundShift}px)`,
				}}
			/>
			<AbsoluteFill
				style={{
					background:
						"repeating-linear-gradient(90deg, transparent 0 36px, rgba(255,255,255,0.018) 36px 37px), linear-gradient(180deg, rgba(255,255,255,0.02), transparent 18%, transparent 82%, rgba(255,255,255,0.02))",
					opacity: 0.7,
				}}
			/>
			<AbsoluteFill
				style={{
					background:
						"radial-gradient(circle at center, transparent 46%, rgba(0,0,0,0.22) 100%), linear-gradient(180deg, rgba(0,0,0,0.44), transparent 24%, transparent 78%, rgba(0,0,0,0.48))",
				}}
			/>
			<AbsoluteFill
				style={{
					background:
						"radial-gradient(circle at 50% 45%, rgba(231,201,146,0.2), transparent 24%), radial-gradient(circle at 50% 45%, rgba(255,244,213,0.08), transparent 40%)",
					opacity: focusPulse,
					mixBlendMode: "screen",
				}}
			/>
			{/* Film Grain Overlay */}
			<AbsoluteFill
				style={{
					opacity: 0.06,
					backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
					mixBlendMode: "overlay",
					pointerEvents: "none",
				}}
			/>
			
			<div
				style={{
					position: "absolute",
					top: 52,
					left: 58,
					right: 58,
					display: "flex",
					alignItems: "center",
					gap: 18,
					opacity: interpolate(frame, [0.08 * fps, 0.8 * fps], [0, 1], {
						extrapolateRight: "clamp",
					}),
					transform: `translateY(${interpolate(frame, [0.08 * fps, 0.8 * fps], [10, 0], {
						extrapolateRight: "clamp",
					})}px)`,
				}}
			>
				<div
					style={{
						display: "flex",
						alignItems: "center",
						gap: 14, // 增加文字与发光线的间距
						flexShrink: 0,
					}}
				>
					<div
						style={{
							width: 32, // 继续加长发光线
							height: 4, // 继续加粗发光线
							borderRadius: 999,
							background: "linear-gradient(90deg, rgba(231,201,146,0.08), rgba(231,201,146,0.96))",
							boxShadow: `0 0 12px rgba(231,201,146,${0.22 * mastheadGlow})`,
						}}
					/>
					<div
						style={{
							fontSize: ipFontSize,
							letterSpacing: `${Math.max(1, Math.round(ipFontSize * 0.06))}px`,
							color: MUTED,
							fontWeight: 600,
							whiteSpace: "nowrap",
						}}
					>
						{ipName}
					</div>
				</div>
				<div
					style={{
						height: 1,
						flex: 1,
						background: "linear-gradient(90deg, rgba(255,255,255,0.58), rgba(255,255,255,0.16), transparent)",
						transform: `scaleX(${mastheadDraw})`,
						transformOrigin: "left",
						opacity: mastheadGlow,
						boxShadow: `0 0 18px rgba(231,201,146,${0.12 * mastheadGlow})`,
					}}
				/>
			</div>
			<div
				style={{
					position: "absolute",
					left: 20,
					right: 20,
					top: "50%",
					transform: `translateY(${quoteOffsetY * 100}%) scale(${cameraZoom})`,
					textAlign: "center",
					fontFamily: SERIF,
				}}
				>
					{quoteLines.map((line, index) => {
						const lineAppearTime = lineAppearTimes[index] ?? 0.5;
						const lineFrameStart = lineAppearTime * fps;
						const entrance = spring({
							fps,
							frame: Math.max(0, frame - lineFrameStart),
							config: {
								damping: 14,
								stiffness: 140,
								mass: 0.8,
							},
					});
					const opacity = interpolate(entrance, [0, 1], [0, 1], {
						extrapolateRight: "clamp",
					});
					const translateY = interpolate(entrance, [0, 1], [40, 0], {
						extrapolateRight: "clamp",
					});
					const scale = interpolate(entrance, [0, 1], [1.1, 1], {
						extrapolateRight: "clamp",
					});

					return (
						<div
							key={`${line}-${index}`}
							style={{
								fontSize: quoteFontSize,
								lineHeight: 1.25,
								fontWeight: 700,
								color: TEXT,
								textShadow: "0 10px 28px rgba(0,0,0,0.38)",
								marginTop: index === 0 ? 0 : lineGap,
								opacity,
								transform: `translateY(${translateY}px) scale(${scale})`,
								position: "relative",
								display: "inline-block",
								padding: "0 20px",
								overflow: "hidden",
							}}
						>
							{(() => {
								const sweepDelay = (lineAppearTime + 0.25) * fps;
								const sweepProgress = interpolate(
									frame,
									[sweepDelay, sweepDelay + 0.5 * fps],
									[0, 1],
									{
										extrapolateLeft: "clamp",
										extrapolateRight: "clamp",
										easing: Easing.out(Easing.cubic),
									},
								);
								const lineSweepTranslate = interpolate(sweepProgress, [0, 1], [-40, 340], {
									extrapolateLeft: "clamp",
									extrapolateRight: "clamp",
								});
								const lineSweepOpacity = interpolate(sweepProgress, [0, 0.2, 0.7, 1], [0, 0.35, 0.3, 0], {
									extrapolateLeft: "clamp",
									extrapolateRight: "clamp",
								});

								return (
									<span
										style={{
											position: "absolute",
											top: "-8%",
											bottom: "-8%",
											left: "-24%",
											width: "36%",
											background:
												"linear-gradient(90deg, rgba(255,255,255,0), rgba(255,244,213,0.15), rgba(255,244,213,0.6), rgba(255,255,255,0))",
											transform: `translateX(${lineSweepTranslate}%) skewX(-18deg)`,
											opacity: lineSweepOpacity,
											mixBlendMode: "screen",
											pointerEvents: "none",
										}}
									/>
								);
							})()}
							{highlightLine(line, focusWords).map((part, partIndex) => {
								const glowOpacity = interpolate(frame, [1.4 * fps, 2.5 * fps], [0, 1], {
									extrapolateLeft: "clamp",
									extrapolateRight: "clamp",
								});
								return (
									<span
										key={`${part.text}-${partIndex}`}
										style={
											part.focused
												? {
													color: ACCENT,
													fontWeight: 900,
													fontStyle: "italic",
													background: `linear-gradient(transparent 64%, rgba(231,201,146,${0.2 + 0.15 * glowOpacity}) 0)`,
													textShadow: `0 0 16px rgba(231,201,146,${0.18 + 0.12 * glowOpacity})`,
													display: "inline-block",
													transform: "scale(1.02)",
													margin: "0 2px",
												}
												: undefined
										}
									>
										{part.text}
									</span>
								);
							})}
						</div>
					);
				})}
			</div>
			<div
				style={{
					position: "absolute",
					left: 0,
					right: 0,
					bottom: 96,
					textAlign: "center",
					fontSize: bookFontSize,
					letterSpacing: `${Math.max(1, Math.round(bookFontSize * 0.08))}px`,
					color: "rgba(236,231,222,0.8)",
					opacity: interpolate(frame, [1.8 * fps, 2.8 * fps], [0, 1], {
						extrapolateLeft: "clamp",
						extrapolateRight: "clamp",
					}),
					transform: `translateY(${interpolate(frame, [1.8 * fps, 2.8 * fps], [12, 0], {
						extrapolateLeft: "clamp",
						extrapolateRight: "clamp",
					})}px)`,
				}}
			>
				{bookTitle}
			</div>
		</AbsoluteFill>
	);
};
