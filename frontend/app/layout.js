import "./globals.css";

export const metadata = {
  title: "Origens - Catálogo e pedidos",
  description: "Catálogo, pedidos, acompanhamento e promoções.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
