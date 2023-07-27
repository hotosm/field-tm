const { EnvironmentPlugin } = require('webpack');
const HtmlWebPackPlugin = require('html-webpack-plugin');
const ModuleFederationPlugin = require('webpack/lib/container/ModuleFederationPlugin');
const TerserPlugin = require('terser-webpack-plugin');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');
const path = require('path');
const deps = require('./package.json').dependencies;
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const WorkboxWebpackPlugin = require('workbox-webpack-plugin'); // Add the WorkboxWebpackPlugin
const CopyPlugin = require('copy-webpack-plugin');

//const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;
module.exports = function (webpackEnv) {
  const isEnvDevelopment = webpackEnv === 'development';
  const isEnvProduction = webpackEnv === 'production';

  return {
    stats: 'errors-warnings',
    cache: true,
    mode: isEnvProduction ? 'production' : isEnvDevelopment && 'development',
    // Stop compilation early in production
    // bail: isEnvProduction,
    devtool: isEnvProduction ? 'source-map' : isEnvDevelopment && 'eval-source-map',
    output: {
      publicPath: `${process.env.FRONTEND_MAIN_URL}/`,
      path: path.resolve(__dirname, 'dist'),
      filename: '[name].[contenthash].bundle.js',
      clean: true,
    },
    resolve: {
      extensions: ['.tsx', '.ts', '.jsx', '.js', '.json'],
    },
    devServer: {
      host: '0.0.0.0',
      port: `${new URL(process.env.FRONTEND_MAIN_URL).port}`,
      historyApiFallback: true,
      allowedHosts: [`${process.env.FRONTEND_MAIN_URL}`],
    },
    module: {
      rules: [
        {
          test: [/\.bmp$/, /\.gif$/, /\.jpe?g$/, /\.png$/, /\.ttf$/, /\.otf$/],
          type: 'asset',
          parser: {
            dataUrlCondition: {
              maxSize: 1000,
            },
          },
        },
        {
          test: /\.m?js/,
          type: 'javascript/auto',
          resolve: {
            fullySpecified: false,
          },
        },
        {
          test: /\.(css|s[ac]ss)$/i,
          use: ['style-loader', 'css-loader', 'postcss-loader'],
        },
        {
          test: /\.(ts|tsx|js|jsx)$/,
          include: path.resolve(__dirname, './src'),
          exclude: /node_modules/,
          use: ['thread-loader', 'babel-loader'],
        },
      ],
    },
    optimization: {
      moduleIds: 'deterministic',
      runtimeChunk: 'single',
      usedExports: true,
      splitChunks: {
        cacheGroups: {
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendors',
            chunks: 'all',
          },
        },
      },
      minimize: isEnvProduction,
      minimizer: [
        // This is only used in production mode
        new TerserPlugin({
          terserOptions: {
            terserOptions: {
              parse: {
                // We want terser to parse ecma 8 code. However, we don't want it
                // to apply minification steps that turns valid ecma 5 code
                // into invalid ecma 5 code. This is why the `compress` and `output`
                ecma: 8,
              },
              compress: {
                ecma: 5,
                warning: false,
                inline: 2,
              },
              mangle: {
                // Find work around for Safari 10+
                safari10: true,
              },
              output: {
                ecma: 5,
                comments: false,
                ascii__only: true,
              },
            },

            // Use multi-process parallel running to improve the build speed
            parallel: true,

            // Enable file caching
            cache: true,
          },
        }),
        // This is only used in production mode
        new CssMinimizerPlugin(),
      ],
    },
    plugins: [
      new CopyPlugin({
        patterns: [
          { from: './public/', to: './' },
          // { from: "other", to: "public" },
        ],
      }),
      // Add the WorkboxWebpackPlugin to generate the service worker and handle caching
      ...(isEnvProduction
        ? new WorkboxWebpackPlugin.GenerateSW({
            clientsClaim: true,
            skipWaiting: true,
            maximumFileSizeToCacheInBytes: 50000000,
          })
        : []),
      //new BundleAnalyzerPlugin(),
      new MiniCssExtractPlugin({
        filename: 'static/css/[name].[contenthash:8].css',
        chunkFilename: 'static/css/[name].[contenthash:8].chunk.css',
      }),
      new ModuleFederationPlugin({
        name: 'fmtm',
        filename: 'remoteEntry.js',
        remotes: {
          map: `fmtm_openlayer_map@${process.env.FRONTEND_MAP_URL}/remoteEntry.js`,
        },
        exposes: {
          './ThemeSlice': './src/store/slices/ThemeSlice.ts',
          './HomeSlice': './src/store/slices/HomeSlice.ts',
          './CommonSlice': './src/store/slices/CommonSlice.ts',
          './LoginSlice': './src/store/slices/LoginSlice.ts',
          './ProjectSlice': './src/store/slices/ProjectSlice.ts',
          './CreateProjectSlice': './src/store/slices/CreateProjectSlice.ts',
          './Store': './src/store/Store.js',
          './BasicCard': './src/utilities/BasicCard.tsx',
          './CustomizedMenus': './src/utilities/CustomizedMenus.tsx',
          './CustomizedSnackbar': './src/utilities/CustomizedSnackbar.jsx',
          './PrimaryAppBar': './src/utilities/PrimaryAppBar.tsx',
          './environment': './src/environment.ts',
          './WindowDimension': './src/hooks/WindowDimension.tsx',
          './OnScroll': './src/hooks/OnScroll.tsx',
          './CoreModules': './src/shared/CoreModules.js',
          './AssetModules': './src/shared/AssetModules.js',
        },
        shared: {
          ...deps,
          react: {
            singleton: true,
            requiredVersion: deps.react,
          },
          'react-dom': {
            singleton: true,
            requiredVersion: deps['react-dom'],
            // requiredVersion: deps["react-dom", "@material-ui/core", "@material-ui/icons"],
          },
        },
      }),
      new HtmlWebPackPlugin(
        Object.assign(
          {},
          {
            inject: true,
            template: './src/index.html',
            favicon: './src/assets/images/favicon.ico',
          },
          // Only for production
          isEnvProduction
            ? {
                minify: {
                  removeComments: true,
                  collapseWhitespace: true,
                  removeRedundantAttributes: true,
                  useShortDoctype: true,
                  removeEmptyAttributes: true,
                  removeStyleLinkTypeAttributes: true,
                  keepClosingSlash: true,
                  minifyJS: true,
                  minifyCSS: true,
                  minifyURLs: true,
                },
              }
            : undefined,
        ),
      ),

      new EnvironmentPlugin(['API_URL', 'FRONTEND_MAIN_URL', 'FRONTEND_MAP_URL']),
    ],
  };
};
