const { EnvironmentPlugin } = require("webpack");
const HtmlWebPackPlugin = require("html-webpack-plugin");
const ModuleFederationPlugin = require("webpack/lib/container/ModuleFederationPlugin");
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
    bail: isEnvProduction,
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
    },

    module: {
      rules: [
        {
          test: [/\.bmp$/, /\.gif$/, /\.jpe?g$/, /\.png$/, /\.ttf$/, /\.otf$/],
          loader: "file-loader",
          options: {
            name: "[name].[ext]",
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
    
    plugins: [
      new ModuleFederationPlugin({
        name: "fmtm_openlayer_map",
        filename: "remoteEntry.js",
        remotes: {
          fmtm: `fmtm@${process.env.FRONTEND_MAIN_URL}/remoteEntry.js`,
        },
        exposes: {
          "./ProjectDetails": "./src/views/Home.jsx",
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
      new HtmlWebPackPlugin({
        template: "./src/index.html",
      }),
      new EnvironmentPlugin(["FRONTEND_MAIN_URL", "FRONTEND_MAP_URL"]),
    ],
  }
};
