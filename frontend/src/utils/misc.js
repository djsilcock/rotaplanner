export function toOrdinal(num) {
  const mod10 = num % 10;
  const mod100 = num % 100;

  if (mod100 > 3 && mod100 < 21) {
    return `${num}th`;
  }
  switch (mod10) {
    case 1:
      return `${num}st`;
    case 2:
      return `${num}nd`;
    case 3:
      return `${num}rd`;
    default:
      return `${num}th`;
  }
}
