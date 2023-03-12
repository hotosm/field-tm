const { EnvironmentPlugin } = require("webpack");
const HtmlWebPackPlugin = require("html-webpack-plugin");
const ModuleFederationPlugin = require("webpack/lib/container/ModuleFederationPlugin");
const TerserPlugin = require('terser-webpack-plugin');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');
const path = require('path');
const deps = require("./package.json").dependencies;
module.exports = function (webpackEnv) {

  const isEnvDevelopment = webpackEnv === 'development';
  const isEnvProduction = webpackEnv === 'production';

  return {
    stats: 'errors-warnings',
    cache: true,
    mode: isEnvProduction ? 'production' : isEnvDevelopment && 'development',
    // Stop compilation early in production
    bail: isEnvProduction,
    devtool: isEnvProduction ? 'source-map' : isEnvDevelopment && 'inline-source-map',
    output: {
      publicPath: `${process.env.FRONTEND_MAIN_URL}/`,
      path: path.resolve(__dirname, "dist"),
      filename: "[name].[contenthash].bundle.js",
      clean:true
    },
    resolve: {
      extensions: [".tsx", ".ts", ".jsx", ".js", ".json"],
    },
    devServer: {
      host: "0.0.0.0",
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
          type: "javascript/auto",
          resolve: {
            fullySpecified: false,
          },
        },
        {
          test: /\.(css|s[ac]ss)$/i,
          use: ["style-loader", "css-loader", "postcss-loader"],
        },
        {
          test: /\.(ts|tsx|js|jsx)$/,
          include: path.resolve(__dirname, './src'),
          exclude: /node_modules/,
          use: [
            'thread-loader',
            'babel-loader'
          ],
        },
      ],
    },
    optimization: {
      moduleIds: 'deterministic',
      runtimeChunk: 'single',
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
            parse: {
              // We want terser to parse ecma 8 code. However, we don't want it
              // to apply any minification steps that turns valid ecma 5 code
              // into invalid ecma 5 code. This is why the 'compress' and 'output'
              // sections only apply transformations that are ecma 5 safe
              // https://github.com/facebook/create-react-app/pull/4234
              ecma: 8,
            },
            compress: {
              ecma: 5,
              warnings: false,
              // Disabled because of an issue with Uglify breaking seemingly valid code:
              // https://github.com/facebook/create-react-app/issues/2376
              // Pending further investigation:
              // https://github.com/mishoo/UglifyJS2/issues/2011
              comparisons: false,
              // Disabled because of an issue with Terser breaking valid code:
              // https://github.com/facebook/create-react-app/issues/5250
              // Pending further investigation:
              // https://github.com/terser-js/terser/issues/120
              inline: 2,
            },
            mangle: {
              safari10: true,
            },
            // Added for profiling in devtools
            // keep_classnames: isEnvProductionProfile,
            // keep_fnames: isEnvProductionProfile,
            output: {
              ecma: 5,
              comments: false,
              // Turned on because emoji and regex is not minified properly using default
              // https://github.com/facebook/create-react-app/issues/2488
              ascii_only: true,
            },
          },
        }),
        // This is only used in production mode
        new CssMinimizerPlugin(),
      ],
    },
    plugins: [
      new ModuleFederationPlugin({
        name: "fmtm",
        filename: "remoteEntry.js",
        remotes: {
           map: `fmtm_openlayer_map@${process.env.FRONTEND_MAP_URL}/remoteEntry.js`,
        },
        exposes: {
          "./ThemeSlice": "./src/store/slices/ThemeSlice.ts",
          "./HomeSlice": "./src/store/slices/HomeSlice.ts",
          "./ProjectSlice": "./src/store/slices/ProjectSlice.ts",
          "./Store": "./src/store/Store.js",
          "./BasicCard": "./src/utilities/BasicCard.tsx",
          "./BasicTabs": "./src/utilities/BasicTabs.tsx",
          "./CustomizedMenus": "./src/utilities/CustomizedMenus.tsx",
          "./CustomizedSnackbar": "./src/utilities/CustomizedSnackbar.jsx",
          "./PrimaryAppBar": "./src/utilities/PrimaryAppBar.tsx",
          "./environment": "./src/environment.ts",
          "./WindowDimension": "./src/hooks/WindowDimension.tsx",
          "./OnScroll": "./src/hooks/OnScroll.tsx",
          "./CoreModules": "./src/shared/CoreModules.js",
          "./AssetModules": "./src/shared/AssetModules.js"
        },
        shared: {
          ...deps,
          react: {
            singleton: true,
            requiredVersion: deps.react,
          },
          "react-dom": {
            singleton: true,
            requiredVersion: deps["react-dom"],
            // requiredVersion: deps["react-dom", "@material-ui/core", "@material-ui/icons"],
          },
        },
      }),
      new HtmlWebPackPlugin({
        template: "./src/index.html",
        favicon: './src/assets/images/favicon.png',
      }),
      new EnvironmentPlugin(["API_URL", "FRONTEND_MAIN_URL", "FRONTEND_MAP_URL"]),
    ],
  }
};
