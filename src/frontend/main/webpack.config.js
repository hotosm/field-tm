const HtmlWebPackPlugin = require("html-webpack-plugin");
const ModuleFederationPlugin = require("webpack/lib/container/ModuleFederationPlugin");

const deps = require("./package.json").dependencies;
module.exports = {
  output: {
    publicPath: "http://localhost:8080/",
  },

  resolve: {
    extensions: [".tsx", ".ts", ".jsx", ".js", ".json"],
  },

  devServer: {
    port: 8080,
    historyApiFallback: true,
  },
  devtool: "source-map",
  module: {
    rules: [
      {
        test: [/\.bmp$/, /\.gif$/, /\.jpe?g$/, /\.png$/, /\.ttf$/, /\.otf$/,],
        loader: 'file-loader',
        options: {
          name: '[name].[ext]',
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
        exclude: /node_modules/,
        use: {
          loader: "babel-loader",
        },
      },
    ],
  },

  plugins: [
    new ModuleFederationPlugin({
      name: "fmtm",
      filename: "remoteEntry.js",
      remotes: {
        map: "fmtm_openlayer_map@http://localhost:8081/remoteEntry.js"
      },
      exposes: {
        "./ThemeSlice": "./src/store/slices/ThemeSlice.ts",
        "./BasicDialog": "./src/utilities/BasicDialog.tsx",
        "./BasicCard": "./src/utilities/BasicCard.tsx",
        "./BasicTabs": "./src/utilities/BasicTabs.tsx",
        "./CustomSwiper": "./src/utilities/CustomSwiper.tsx",
        "./CustomizedMenus": "./src/utilities/CustomizedMenus.tsx",
        "./PrimaryAppBar":"./src/utilities/PrimaryAppBar.tsx",
        "./environment": "./src/environment.ts",
        "./WindowDimension":"./src/hooks/WindowDimension.tsx"
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
  ],
};
