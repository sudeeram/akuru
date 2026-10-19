'use client';
import { useId } from 'react';
import type { AvatarConfig } from '@/api/avatars/avatar.types';
import { avatarCatalogue, parseAvatar } from '@/lib/student-avatar';

/** Original layered AKURU artwork. Paths and colours come only from our finite catalogue. */
export function StudentAvatar({
  avatar,
  fallback = 'A',
  className = '',
  label,
}: {
  avatar?: AvatarConfig | null;
  fallback?: string;
  className?: string;
  label?: string;
}) {
  const id = useId().replace(/:/g, '');
  const a = parseAvatar(avatar);
  if (!a)
    return (
      <span
        className={`student-avatar avatar-initials ${className}`}
        role={label ? 'img' : undefined}
        aria-label={label}
        aria-hidden={!label}
      >
        {fallback}
      </span>
    );
  const palette = avatarCatalogue.options;
  const skin = palette.skin[a.skin].color,
    hair = palette.hairColor[a.hairColor].color;
  const clothes = palette.clothesColor[a.clothesColor].color;
  const face = {
    soft: 'M48 81 C46 43 70 38 100 39 C130 38 154 47 152 81 L150 119 C146 145 120 165 100 167 C80 165 54 145 50 119Z',
    round:
      'M46 82 C43 47 68 37 100 38 C132 37 157 47 154 82 L153 117 C151 148 126 166 100 166 C74 166 49 148 47 117Z',
    oval: 'M49 81 C47 45 72 37 100 38 C128 37 153 45 151 81 L148 118 C142 148 116 171 100 173 C84 171 58 148 52 118Z',
    full: 'M44 80 C43 46 67 37 100 38 C133 37 157 46 156 80 L155 113 C160 139 138 163 118 167 Q100 172 82 167 C62 163 40 139 45 113Z',
  }[a.face];
  const backHair = ['waves', 'bob', 'braids', 'bun'].includes(a.hair);
  return (
    <span className={`student-avatar ${className}`}>
      <svg
        viewBox="0 0 200 220"
        role={label ? 'img' : undefined}
        aria-label={label}
        aria-hidden={!label}
        focusable="false"
        data-avatar-version="1"
      >
        {label && <title>{label}</title>}
        <defs>
          <clipPath id={`${id}-crop`}>
            <rect width="200" height="220" rx="32" />
          </clipPath>
          <clipPath id={`${id}-face`}>
            <path d={face} />
          </clipPath>
          <linearGradient id={`${id}-skin`} x2="0.8" y2="1">
            <stop stopColor="#fff" stopOpacity=".12" />
            <stop offset="1" stopColor="#823d26" stopOpacity=".12" />
          </linearGradient>
        </defs>
        <g clipPath={`url(#${id}-crop)`}>
          <rect
            width="200"
            height="220"
            fill={palette.background[a.background].color}
          />
          <circle cx="164" cy="26" r="80" fill="#fff" opacity=".14" />
          {backHair && (
            <g fill={hair}>
              {a.hair === 'bun' ? (
                <>
                  <circle cx="102" cy="26" r="25" />
                  <path d="M40 87Q28 40 63 29Q110 6 146 38Q169 52 159 114L143 152H56Z" />
                </>
              ) : a.hair === 'braids' ? (
                <>
                  <path d="M40 90Q26 24 100 25Q170 24 160 96L148 143H52Z" />
                  {[0, 1, 2, 3, 4, 5].map((n) => (
                    <g key={n}>
                      <ellipse
                        cx={43 + (n % 2) * 3}
                        cy={111 + n * 13}
                        rx="13"
                        ry="12"
                      />
                      <ellipse
                        cx={157 - (n % 2) * 3}
                        cy={111 + n * 13}
                        rx="13"
                        ry="12"
                      />
                    </g>
                  ))}
                </>
              ) : a.hair === 'bob' ? (
                <path d="M38 73Q27 40 60 27Q88 12 113 23Q153 19 165 55Q177 68 165 92Q183 111 167 134Q180 158 154 169L44 168Q16 150 35 129Q17 112 35 92Z" />
              ) : (
                <path d="M40 79Q23 36 68 24Q105 8 135 32Q171 36 164 80Q186 98 167 120Q188 141 170 164Q187 184 163 207H35Q12 188 31 166Q9 142 32 123Q15 98 40 79Z" />
              )}
            </g>
          )}
          <path
            d="M-9 225Q2 188 49 181L78 169H122L151 181Q198 188 209 225Z"
            fill={clothes}
          />
          {a.outfit === 'hoodie' && (
            <>
              <path
                d="M51 182Q52 156 77 163L99 180L122 163Q149 156 150 183L125 203H75Z"
                fill={clothes}
              />
              <path
                d="M55 180L79 191L99 183L121 191L146 179L128 204H72Z"
                fill="#fff"
                opacity=".2"
              />
              <path
                d="M75 196V220M125 196V220"
                stroke="#fff"
                strokeWidth="3"
                opacity=".65"
                strokeLinecap="round"
              />
            </>
          )}
          <path d="M79 147V176Q100 194 121 176V147" fill={skin} />
          <path
            d="M79 150Q99 175 121 150V164Q100 183 79 163Z"
            fill="#763e28"
            opacity=".14"
          />
          {a.outfit === 'tee' && (
            <path
              d="M70 176Q100 204 130 176L137 181Q100 217 63 181Z"
              fill="#000"
              opacity=".09"
            />
          )}
          {a.outfit === 'collar' && (
            <>
              <path
                d="M77 172L100 189L81 207L65 180ZM123 172L100 189L119 207L135 180Z"
                fill="#fff"
                opacity=".65"
              />
              <path
                d="M100 189V220"
                stroke="#fff"
                opacity=".5"
                strokeWidth="2"
              />
            </>
          )}
          <g fill={skin}>
            <ellipse cx="46" cy="107" rx="16" ry="22" />
            <ellipse cx="154" cy="107" rx="16" ry="22" />
          </g>
          <g
            stroke="#7b3e29"
            opacity=".22"
            strokeWidth="4"
            fill="none"
            strokeLinecap="round"
          >
            <path d="M48 99Q35 94 39 112L45 116M152 99Q165 94 161 112L155 116" />
          </g>
          <path d={face} fill={skin} />
          <path d={face} fill={`url(#${id}-skin)`} />
          <g clipPath={`url(#${id}-face)`}>
            <ellipse
              cx="44"
              cy="119"
              rx="20"
              ry="50"
              fill="#793c29"
              opacity=".07"
            />
            <ellipse
              cx="65"
              cy="128"
              rx="13"
              ry="6"
              fill="#c65a4c"
              opacity=".1"
            />
            <ellipse
              cx="135"
              cy="128"
              rx="13"
              ry="6"
              fill="#c65a4c"
              opacity=".1"
            />
          </g>
          <g fill="none" stroke={hair} strokeWidth="6" strokeLinecap="round">
            {a.brows === 'arched' ? (
              <>
                <path d="M60 88Q73 76 87 87M113 87Q128 76 140 88" />
              </>
            ) : a.brows === 'gentle' ? (
              <>
                <path d="M60 88Q75 80 87 87M113 87Q127 80 140 88" />
              </>
            ) : (
              <>
                <path d="M60 86L86 85M114 85L140 86" />
              </>
            )}
          </g>
          {([74, 126] as const).map((x, index) => (
            <g key={x}>
              {a.eyes === 'smile' ? (
                <path
                  d={`M${x - 13} 106Q${x} 91 ${x + 13} 106`}
                  fill="none"
                  stroke="#352b33"
                  strokeWidth="4"
                  strokeLinecap="round"
                />
              ) : (
                <>
                  {a.eyes === 'round' ? (
                    <ellipse cx={x} cy="107" rx="15" ry="14" fill="#fffaf4" />
                  ) : (
                    <path
                      d={`M${x - 17} 106Q${x - 2} ${a.eyes === 'upturned' ? 91 : 88} ${x + 17} 103Q${x + 7} 122 ${x - 9} 115Z`}
                      fill="#fffaf4"
                    />
                  )}
                  <ellipse
                    cx={x + 2}
                    cy="106"
                    rx="9"
                    ry={a.eyes === 'round' ? 12 : 11}
                    fill={palette.eyeColor[a.eyeColor].color}
                  />
                  <ellipse cx={x + 3} cy="106" rx="5" ry="8" fill="#27232c" />
                  <ellipse cx={x} cy="101" rx="3" ry="3.5" fill="#fff" />
                  <path
                    d={
                      a.eyes === 'round'
                        ? `M${x - 13} 101Q${x} 86 ${x + 14} 100`
                        : `M${x - 17} 106Q${x - 2} ${a.eyes === 'upturned' ? 91 : 88} ${x + 17} 103`
                    }
                    fill="none"
                    stroke="#352b33"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                  />
                  {a.eyes === 'upturned' && (
                    <path
                      d={
                        index === 0
                          ? `M${x - 15} 103L${x - 21} 99`
                          : `M${x + 14} 101L${x + 20} 97`
                      }
                      stroke="#352b33"
                      strokeWidth="2.5"
                    />
                  )}
                </>
              )}
            </g>
          ))}
          {a.face === 'full' ? (
            <>
              <ellipse
                cx="100"
                cy="127"
                rx="7"
                ry="4"
                fill="#a35837"
                opacity=".3"
              />
              <path
                d="M96 128Q100 131 104 128"
                fill="none"
                stroke="#a65e3c"
                strokeWidth="1.5"
              />
            </>
          ) : (
            <path
              d="M92 126Q100 133 108 126Q101 124 92 126"
              fill="#9b5534"
              opacity=".45"
            />
          )}
          {a.mouth === 'open' ? (
            <>
              <path
                d="M81 141Q100 150 120 141Q111 166 97 161Q85 159 81 141"
                fill="#6c3031"
              />
              <path
                d="M84 143Q100 150 117 143L112 149Q99 154 88 148Z"
                fill="#fff9ed"
              />
              <path d="M96 158Q105 153 111 157Q101 165 96 158" fill="#d88581" />
            </>
          ) : a.mouth === 'grin' ? (
            <>
              <path
                d="M80 142Q99 150 120 139Q114 158 99 158Q86 156 80 142"
                fill="#793b37"
              />
              <path
                d="M84 144Q102 150 116 142L111 148Q98 153 87 148Z"
                fill="#fff9ed"
              />
            </>
          ) : a.mouth === 'calm' ? (
            <path
              d="M90 145Q100 148 110 145"
              fill="none"
              stroke="#9a503b"
              strokeWidth="2.5"
              strokeLinecap="round"
            />
          ) : (
            <>
              <path d="M82 142Q99 151 118 141Q103 154 91 147Z" fill="#a45b48" />
              <path
                d="M85 142Q100 148 115 142"
                fill="none"
                stroke="#7e4036"
                strokeWidth="1.5"
              />
            </>
          )}
          <g fill={hair}>
            {a.hair === 'sweep' && (
              <>
                <path d="M41 87Q25 61 43 39Q32 35 39 23Q59 29 77 20Q113 5 138 22L157 18Q158 32 149 38L170 38Q165 51 154 55L171 59Q156 72 149 87L144 63Q124 71 104 47Q87 71 59 65L53 92Z" />
                <path
                  d="M52 45Q85 27 113 30Q99 41 83 44Q64 44 52 59Z"
                  fill="#fff"
                  opacity=".06"
                />
              </>
            )}
            {a.hair === 'curls' && (
              <>
                {[
                  [48, 57],
                  [45, 40],
                  [58, 31],
                  [74, 27],
                  [90, 25],
                  [108, 25],
                  [126, 28],
                  [143, 35],
                  [155, 47],
                  [153, 65],
                  [43, 76],
                  [59, 51],
                  [78, 48],
                  [98, 43],
                  [116, 45],
                  [135, 51],
                  [133, 65],
                  [112, 59],
                  [88, 58],
                  [67, 65],
                ].map(([cx, cy], i) => (
                  <circle
                    key={i}
                    cx={cx}
                    cy={cy}
                    r={12 + (i % 3)}
                    fill={i % 3 === 0 ? hair : undefined}
                  />
                ))}
                <path d="M42 78L47 91L54 72M149 73L151 91L157 72" />
              </>
            )}
            {a.hair === 'waves' && (
              <>
                <path d="M40 99Q26 60 56 39Q78 21 104 29Q125 18 147 39Q171 62 158 108Q153 76 130 70Q111 62 104 44Q87 72 60 81Q48 88 40 108Z" />
                <path
                  d="M62 50Q81 30 101 34Q75 66 53 77Q61 60 62 50"
                  fill="#fff"
                  opacity=".06"
                />
              </>
            )}
            {a.hair === 'bob' && (
              <>
                <path d="M37 106Q24 76 40 56Q33 32 63 30Q83 13 108 30Q138 18 156 44Q178 58 163 83L166 104Q155 88 142 83Q120 76 106 45Q92 75 61 81Q44 85 37 106Z" />
                <path
                  d="M53 53Q70 30 91 33Q71 52 57 67Z"
                  fill="#fff"
                  opacity=".06"
                />
              </>
            )}
            {a.hair === 'crop' && (
              <path d="M43 89Q32 52 50 35Q78 15 102 23Q139 15 154 44L158 84L146 69L141 48L124 58L105 48L88 58L69 49L55 69L51 89Z" />
            )}
            {a.hair === 'bun' && (
              <path d="M43 91Q31 50 66 33Q111 14 143 41Q168 59 156 92L146 73Q121 67 101 40Q83 67 55 72Z" />
            )}
            {a.hair === 'braids' && (
              <>
                <path d="M43 94Q30 50 63 33Q100 14 140 36Q170 57 157 94L145 74Q119 65 101 41Q81 67 54 75Z" />
                <path
                  d="M100 31Q82 50 52 65M103 31Q121 53 150 66"
                  fill="none"
                  stroke="#fff"
                  strokeOpacity=".1"
                  strokeWidth="3"
                />
              </>
            )}
          </g>
          {a.glasses !== 'none' && (
            <g
              fill="none"
              stroke={a.glasses === 'round' ? '#EDD5C0' : '#45405A'}
              strokeWidth="3"
              strokeLinejoin="round"
            >
              {a.glasses === 'round' ? (
                <>
                  <circle cx="74" cy="107" r="21" />
                  <circle cx="126" cy="107" r="21" />
                </>
              ) : a.glasses === 'square' ? (
                <>
                  <rect x="51" y="89" width="44" height="35" rx="10" />
                  <rect x="105" y="89" width="44" height="35" rx="10" />
                </>
              ) : (
                <>
                  <path d="M49 88L95 94L92 120Q67 134 55 115Z" />
                  <path d="M151 88L105 94L108 120Q133 134 145 115Z" />
                </>
              )}
              <path d="M95 104Q100 100 105 104M51 103L42 99M149 103L158 99" />
            </g>
          )}
        </g>
      </svg>
    </span>
  );
}
