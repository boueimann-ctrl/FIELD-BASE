# FIELD//BASE

> **FIND YOUR FIELD. BUILD YOUR BASE.**

FIELD//BASEは、サバイバルゲームを始めたい初心者から経験者まで、  
自分に合ったフィールドやショップを探しやすくすることを目指して開発しているWebアプリケーションです。

現在、個人開発として設計・開発を進めています。

---

## 📌 Overview

サバイバルゲームに興味を持っても、実際に参加しようとすると、

- 近くにどんなフィールドがあるのか
- 料金はいくらなのか
- 装備を持っていなくても参加できるのか
- 初心者でも参加しやすいのか
- 電車や車でどのくらいかかるのか
- 近くにショップがあるのか

といった情報を自分で複数のサイトから探す必要があります。

FIELD//BASEでは、フィールドの場所・料金・レンタル・アクセスなどの情報をまとめ、

**「サバゲーに行ってみたい」と思った人が、実際にフィールドへ行くまでのハードルを下げること**

を目標としています。

---

## 🎯 Concept

FIELD//BASEでは、

**「初心者に優しく、経験者にも便利なサバゲー情報基盤」**

をコンセプトにしています。

単純なフィールド一覧ではなく、

**現在地 → フィールドを探す → 比較する → 詳細を見る → 実際に行く**

までを一つのサービスで完結できることを目指しています。

---

## ✨ Features

### Implemented

- [x] Landing Page
- [x] Login Page
- [x] Email入力バリデーション
- [x] Password入力バリデーション
- [x] React Routerによるページルーティング

### Roadmap

- [ ] Register Page
- [ ] ユーザー認証
- [ ] Map Page
- [ ] 現在地取得
- [ ] 周辺フィールド検索
- [ ] Field Detail Page
- [ ] Shop Search
- [ ] Contact Page
- [ ] フィールド料金・レンタル情報
- [ ] 現在地からフィールドまでの距離表示
- [ ] 移動手段別のアクセス情報

---

## 🛠 Tech Stack

### Frontend

- React
- TypeScript
- Vite
- React Router

### Development

- Git
- GitHub
- VS Code
- npm

---

## 🏗 Directory Structure

```text
FIELD-BASE/
├── frontend/
├── backend/
├── docs/
└── README.md
```

Frontend / Backend / Documentationを分離し、プロジェクトの規模が大きくなっても管理しやすい構成を目指しています。

---

## 🚀 Setup

### 1. Clone Repository

```bash
git clone https://github.com/boueimann-ctrl/FIELD-BASE.git
```

### 2. Move to Frontend

```bash
cd FIELD-BASE/frontend
```

### 3. Install Dependencies

```bash
npm install
```

### 4. Start Development Server

```bash
npm run dev
```

起動後、ターミナルに表示されるローカルURLへアクセスしてください。

---

## 💡 Why I Built This

個人開発のテーマを考える中で、自分自身が興味を持っているサバイバルゲームに着目しました。

サバイバルゲームについて調べていくと、フィールド・料金・レンタル・アクセス・ショップなどの情報が複数の場所に分散しており、初心者にとって「どこに行けばいいのか」を判断するまでのハードルが高いと感じました。

そこで、これらの情報を一つにまとめ、現在地を起点として自分に合ったフィールドを探せるサービスとしてFIELD//BASEの開発を始めました。

また、このプロジェクトを通して、Webアプリケーションがどのような技術の組み合わせで動いているのかを理解しながら、自分で設計・実装できる力を身につけることも目標としています。

---

## 📚 What I'm Learning

FIELD//BASEでは、現在主に以下について学びながら開発しています。

- ReactによるUIの構築
- TypeScriptによる型を意識した開発
- React Routerによるページルーティング
- フォームの状態管理
- 入力値のバリデーション
- Git / GitHubによるバージョン管理
- コンポーネントを利用したUI設計
- HTML / CSS / JavaScriptとReactの関係

単純にコードを動かすだけではなく、

**「なぜこのコードが必要なのか」「内部でどのように動いているのか」**

を理解しながら開発することを意識しています。

---

## 🗺 Development Roadmap

```text
Landing Page
      ↓
Login Page
      ↓
Register Page
      ↓
Authentication
      ↓
Map
      ↓
Field Search
      ↓
Field Detail
      ↓
Shop Search
      ↓
Backend / Database
      ↓
Deploy
```

現在はFrontendを中心に開発を進めています。

---

## 📸 Screenshots

UIの開発に合わせて、アプリケーションのスクリーンショットを追加予定です。

---

## 📈 Development Status

**Status: 🚧 Under Development**

FIELD//BASEは現在開発中です。

機能を増やすことだけを目的とせず、実装した技術の仕組みを理解しながら継続的に開発しています。

---

## 👤 Author

**boueimann-ctrl**

GitHub:  
https://github.com/boueimann-ctrl

---

## 📄 License

Licenseについては今後決定予定です。