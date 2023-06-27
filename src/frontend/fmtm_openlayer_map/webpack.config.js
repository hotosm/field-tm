const { EnvironmentPlugin } = require("webpack");
const HtmlWebPackPlugin = require("html-webpack-plugin");
const ModuleFederationPlugin = require("webpack/lib/container/ModuleFederationPlugin");
// const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');
const TerserPlugin = require('terser-webpack-plugin');
const path = require('path');
const deps = require("./package.json").dependencies;
module.exports = (webpackEnv) => {
  const isEnvDevelopment = webpackEnv === 'development';
  const isEnvProduction = webpackEnv === 'production';
  return {
    stats: 'errors-warnings',
    cache: true,
    mode: isEnvProduction ? 'production' : isEnvDevelopment && 'development',
    // Stop compilation early in production
    // bail: isEnvProduction,
    devtool: isEnvProduction ? 'source-map' : isEnvDevelopment && 'inline-source-map',
    output: {
      publicPath: `${process.env.FRONTEND_MAP_URL}/`,
      path: path.resolve(__dirname, "dist"),
      filename: "[name].[contenthash].bundle.js",
      clean:true
    },
    devtool: "source-map",
    resolve: {
      extensions: [".tsx", ".ts", ".jsx", ".js", ".json"],
    },

    devServer: {
      host: "0.0.0.0",
      port: `${new URL(process.env.FRONTEND_MAP_URL).port}`,
      historyApiFallback: true,
      allowedHosts: [`${process.env.FRONTEND_MAP_URL}`],
      headers:{
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept',
      },
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
          use: ["style-loader", "css-loader", "postcss-loader", "sass-loader"],
        },
        {
          test: /\.(ts|tsx|js|jsx)$/,
          exclude: /node_modules/,
          use: {
            loader: "babel-loader",
          },

        },
      ],
    },
    optimization: {
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
              }
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
      // new BundleAnalyzerPlugin(),
      new ModuleFederationPlugin({
        name: "fmtm_openlayer_map",
        filename: "remoteEntry.js",
        remotes: {
          fmtm: `fmtm@${process.env.FRONTEND_MAIN_URL}/remoteEntry.js`,
        },
        exposes: {
          "./ProjectDetails": "./src/views/Home.jsx",
          "./Submissions": "./src/views/Submissions.jsx",
          "./DefineAreaMap": "./src/views/DefineAreaMap.jsx",
          "./Tasks": "./src/views/Tasks.jsx",
          "./ProjectInfo": "./src/views/ProjectInfo.jsx",
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
          },
        },
      }),
      new HtmlWebPackPlugin(
        Object.assign(
          {},
          {
            inject: true,
            template: "./src/index.html",
          },
          // Only for production
          isEnvProduction ? {
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
            minifyURLs: true
          }
        } : undefined
        )
      ),
      new EnvironmentPlugin(["FRONTEND_MAIN_URL", "FRONTEND_MAP_URL"]),
    ],
  }
};
